#!/usr/bin/env pypy3
"""
Optimizer, written as a data miner.  Break the data up into regions
of 'bad' and 'better'. Find ways to jump from 'bad' to 'better'. 
Nearly all this processing takes loglinear time.

    :-------:  
    | Ba    | Bad <----.  planning= (better - bad)
    |    56 |          |  monitor = (bad - better)
    :-------:------:   |  
            | B    |   v  
            |    5 | Better  
            :------:  

Copyright (c) 2020, Tim Menzies. All rights (BSD 2-Clause license).

## Overview

Is your software ethical?  Does its own source code  holds a
representation of user goals and  uses those at runtime to guide
its own behavior?  Can that software report how well the user goals
are being achieved and can it suggest how to adjust the system, to
better achieve those goals?

Do you want to make your software more ethical?  BRKNBAD is a
collection of data structures that support ethical the kind of
ethical reasoning listed above.  It is a multi-objective optimizer
that reasons by breaking up problems into regions of `bad` and
`better`, then looks for ways on how to jump between those regions.

BRKNBAD might be an ethical choice in domains:

- when users have to trade-off competing goals, 
- when succinct explanations are needed about what the system is doing,
- when  those explanations have to include ranges within which it is safe
  to change the system, 
- when guidance is needed for how to improve things
  (or know what might make things worse); 
- when thing being studied is constantly changing so:
   - we have to perpetually check if the current system is still trustworthy
   - and, if not, we need to update our models

Technical notes: 

- `bad` and `better` are score via 
  [Zitler's continuous domination predicate](#brknbad.Tab.dom).
- Examples are clustered in goal
  space and the `better` cluster is the one that dominates all the
  other `bad` clusters.
- Numerics are then broken up into just a few ranges
  using a bottom-up merging process
  guided by the ratio of `better` to `bad`  in each range. 
- These numeric ranges,
  and the symbolic ranges are then used to build a succinct decision list
  that can explain what constitutes `better` behavior. 
  This decision list has many uses:
    - _Planning_: The deltas in the conditions that lead to the leaves of that decision list can
      offer guidance on how to change
      `bad` to `better`. 
    - _Monitoring_: The opposite of planning. Learn what can change `better`
      to `bad`, then watch out for those things.
    - _Anomaly detection and incremental certification:_ 
     The current decision list can be trusted as long as new examples 
     fall close to the old examples seen in the leaves of the decision list.
    - _Stream mining_: Stop learning while the anomaly detector is not
      triggering. Track the anomalies seen each branch of the decision list.
      Update just the branches that get too many anomalies (if that ever happens).

## Classes

In my code `Thing` and `o` are basic utility classes. `Thing`s
know how to pretty-print themselves while `o` classes are
basic containers for things with names slots (but no methods).

     Thing
        o  
        Cluster
           Bore     :has 1 :to 2 :of Tab
           Tree     :has 1 :to * :of Tab
        Col(txt, pos)
           Num(mu, lo, hi)
           Sym(mode)
        Cols        :has 1 :to * :of Col
        Dist        :has 1 :to 1 :of Tab
        Range(lo, hi)
        Ranges      :has 1 :to * :of Range
        Tab(rows)   :has 1 :to 1 :of Cols  
        Test

The real work here is done by `Tab`les. 
Such `Tab`les are the core of this design.
When data is read from disk
it is entered into a `Tab`le. When collecting data from some
process, that data is incrementally written into a `Tab`le.
If we recursively cluster data, each level of that recursion
is a table.
into tables. that have `rows` and `cols`.
Each row is some example of `y=f(x)` where `y` and `x`
can have multiple values (and when `|y|>1`, then this
then becomes a multi-objective reasoner).

Our  `rows` are just plain old Python lists. We can
compute the `dist`ance between rows as well as checking
if the goals in one row are "better than" (also known as
"dominates") the other.

`Col` objects summarize what was seen in each column. There are
two general kinds of `Col`s (`Num`erics and `Sym`bols) and
which can be categoriesed into

- `y` values:
 - numeric goals (that we might want to maximize or minimze)
 - symbolic gaols (that are also called `klass`es)
- `x` values:
 - which can be numeric or symbolic.

## License

MIT License

Copyright (c) 2020, Tim Menzies

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the
Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall
be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import traceback,argparse,random,pprint,math,sys,re,os

def help(): 
  """
  Define options.
  """
  h = makeArgParseOption
  return [
    h("verbose mode for Tree",                          treeVerbose= False),
    h("bin min size =len**b",                           b= .5),
    h("what columns to while tree building " ,          c= ["x","y"]),
    h("use at most 'd' rows for distance calcs",        d= 256),
    h("merge ranges whose scores differ by less that F",e= 0.05),
    h("separation of poles (f=1 means 'max distance')", f= .9),
    h("coefficient for distance" ,                      p= 2),
    h("random number seed" ,                            r = 1),
    h("tree leaves must be at least n**s in size" ,     s= 0.5),
    h("training data (arff format",                     train= "train.csv"),
    h("testing data (csv format)",                      test=  "test.csv"),
    h("List all tests.",                                L = False),
    h("Run all tests.",                                 T = False),
    h("Run just the tests with names matching 'S'",     t= "")
  ]

def makeArgParseOption(txt,**d):
  """
  Support code for Command-line Options. Argument
  types are inferred by peeking at the default.
  Different types then lead to different kinds of options.
  """
  for k in d:
    key = k
    val = d[k]
    break
  default = val[0] if isinstance(val,list)  else val
  if val is False :
    return key,default,dict(help=txt, action="store_true")
  else:
    m,t = "S",str
    if isinstance(default,int)  : m,t= "I",int
    if isinstance(default,float): m,t= "F",float
    if isinstance(val,list):
      return key,default,dict(help=txt, choices=val,          
                      default=default, metavar=m ,type=t)
    else:
      eg = "; e.g. -%s %s"%(key,val) if val != "" else ""
      return key,default, dict(help=txt + eg,
                      default=default, metavar=m, type=t)
  
def args(f):
  """
  Link to Python's command line option processor.
  """
  lst = f()
  before = re.sub(r"\n  ","\n", __doc__)
  before = before.split('\n\n')[0]
  parser = argparse.ArgumentParser(description = before,
             formatter_class = argparse.RawDescriptionHelpFormatter)
  for key, _,args in lst:
    parser.add_argument("-"+key,**args)
  return parser.parse_args()

#---------------------------------------------------------

class Magic:
  """
  Define magic characterss. 
  Used in column headers to denote goals, klasses, numbers.
  Used also to denote things to skip (columns, specific cells).
  """
  def no(s): 
    "Things to skip."
    return  s == "?"
  def nump(s): 
    "Numbers."
    return "<" in s or "$" in s or ">" in s
  def goalp(s): 
    "Goals"
    return "<" in s or "!" in s or ">" in s
  def klassp(s): 
    "Non-numeric goals."
    return "!" in s
  def lessp(s): 
    "Thing to minimize"
    return "<" in s
  
#---------------------------------------------------------
### Thing
# Python objects have *very* uninformative print strings.
# `Thing`s know how to present themselves.
class Thing:
  """
  All my classes are Things that pretty print themselves
  by reporting themselves as nested dictionaries then 
  pprint-ing that dictionary.
  """
  def __repr__(i):
     return re.sub(r"'",' ', 
                   pprint.pformat(dicts(i.__dict__),compact=True))

def dicts(i,seen=None):
  """
  This is a tool used by `Thing`.
  Converts `i` into a nested dictionary, then pretty-prints that.
  """
  if isinstance(i,(tuple,list)): 
    return [ dicts(v,seen) for v in i ]
  elif isinstance(i,dict): 
    return { k:dicts(i[k], seen) for k in i if str(k)[0] !="_"}
  elif isinstance(i,Thing): 
    seen = seen or {}
    j =id(i) % 128021 # ids are LONG; show them shorter.
    if i in seen: return f"#:{j}"
    seen[i]=i
    d=dicts(i.__dict__,seen)
    d["#"] = j
    return d
  else:
    return i

class o(Thing):
  def __init__(i,**d) : i.__dict__.update(**d)

my  = o(**{k:d for k,d,_ in help()})

class Col(Thing):
  def __init__(i,pos,txt):
    i.n, i.pos, i.txt = 0, pos, txt
    i.w = -1 if Magic.lessp(txt) else 1
  def __add__(i,x):
    if Magic.no(x): return x
    i.n += 1
    return i.add(x)

class Num(Col):
  def __init__(i, *l):
    super().__init__(*l)
    i.mu, i.lo, i.hi = 0, 10**32, -10**32
  def mid(i): return i.mu
  def add(i,x):
    x = float(x)
    i.lo,i.hi = min(i.lo,x), max(i.hi,x)
    i.mu      = i.mu + (x - i.mu)/i.n
    return x
  def norm(i,x):
    if Magic.no(x) : return x
    return (x - i.lo)  / (i.hi - i.lo + 0.000001)
  def dist(i,x,y):
    if Magic.no(x) and Magic.no(y): return 1
    if Magic.no(x): x = i.lo if y > i.mu else i.hi
    if Magic.no(y): y = i.lo if x > i.mu else i.hi
    return abs(i.norm(x) - i.norm(y))

class Sym(Col):
  def __init__(i, *l):
    super().__init__(*l)
    i.seen, i.most, i.mode = {}, 0, None
  def mid(i): return i.mode
  def add(i,x):
    tmp = i.seen[x] = i.seen.get(x,0) + 1
    if tmp > i.most: i.most,i.mode = tmp,x
    return x
  def dist(i,x,y): 
    return 1 if Magic.no(x) and Magic.no(y) else x != y
 
class Cols(Thing):
  def __init__(i) : 
    i.x,i.y,i.nums,i.syms,i.all,i.klas = {},{},{},{},[],None
  def add(i,lst): 
    [ col.add( lst[col.pos] ) for col in i.all ]
  def klass(i,lst): 
    return lst[i.klas]
  def header(i,lst):
    for pos,txt in enumerate(lst):
      tmp = (Num if Magic.nump(txt) else Sym)(pos,txt)
      i.all += [tmp]
      (i.y    if Magic.goalp(txt) else i.x)[pos] = tmp
      (i.nums if Magic.nump(txt)  else i.syms)[pos] = tmp
      if Magic.klassp(txt) : i.klas  = tmp

class Tab(Thing):
  def __init__(i,rows=[]):
    i.rows, i.cols = [], Cols()
    [i.add(row) for row in rows]
  def clone(i,rows=[]):
    t  = Tab()
    t  + [c.txt for c in i.cols.all] 
    [t + row for row in  rows]
    return t
  def __add__(i,a): 
    return i.add(a) if i.cols.all else i.cols.header(a)
  def add(i,a): 
    i.rows += [[c + a[c.pos] for c in i.cols.all]]
  def read(i,data=None): 
    [i + row for row in cols(rows(data))]
    return i
  def pairs(i,col):
    return Bins(col.pos,i.rows, lambda z: z[col.pos], 
                                lambda z: i.cols.klass(z))
  def status(i):
    return '{' + ', '.join([('%.2f' % c.mid()) 
                     for c in i.cols.y.values()]) + '}'
  def mid(i):
    return [ col.mid() for col in i.cols.all ]
  def better(i,row1,row2):
    s1,s2,n = 0,0,len(i.cols.y)+0.0001
    for c in i.cols.y.values():
      x   = c.norm( row1[c.pos] )
      y   = c.norm( row2[c.pos] )
      s1 -= math.e**(c.w*(x-y)/n)
      s2 -= math.e**(c.w*(y-x)/n)
    return s1/n < s2/n

class Dist(Thing):
  def __init__(i, t,cols=None, rows=None, p=my.p):
    i.t= t
    i.p= p
    i.cols = cols or t.cols.x
    i.rows = rows or shuffle(t.rows)[:my.d]
  def dist(i,row1,row2):
    d = 0
    for col in i.cols.values():
      inc = col.dist( row1[col.pos], row2[col.pos] )
      d  += inc**my.p
    return (d/len(i.cols))**(1/my.p)
  def neighbors(i,r1):
    a = [(i.dist(r1,r2),r2) for r2 in i.rows if id(r1) != id(r2)]
    return sorted(a, key = lambda z: z[0])
  def faraway(i,row):
     a= i.neighbors(row)
     return a[ int( len(a) * my.f ) ][1]
  def poles(i):
     tmp   = random.choice(i.rows)
     left  = i.faraway(tmp)
     right = i.faraway(left)
     return left, right, i.dist(left,right)
  def project(i,row, left,right,c):
     a = i.dist(row,left)
     b = i.dist(row,right)
     d = (a**2 + c**2 - b**2) / (2*c)
     if d>1: d= 1
     if d<0: d= 0
     return d

class Cluster(Thing): pass

class Tree(Cluster):
  def __init__(i, t, cols=my.c, lo=None, lvl=0):
    lo = lo or 2*len(t.rows)**my.s
    if len(t.rows) > lo:
      if my.treeVerbose:
        print(('| '*lvl) + str(len(t.rows)))
      i.d         = Dist(t,cols=t.cols.__dict__[cols])
      i.l,i.r,i.c = i.d.poles()
      xs          = [i.d.project(r,i.l,i.r,i.c) for r in t.rows]
      i.mid       = sum(xs) / len(xs)
      i.kids      = [t.clone(),t.clone()]
      [i.kids[x >= i.mid].add(r)     for x,r in zip(xs, t.rows)]
      if len(i.kids[0].rows) < len(t.rows) and \
         len(i.kids[1].rows) < len(t.rows) :
         [ Tree(kid, cols=cols, lo=lo, lvl=lvl+1) 
            for kid in i.kids ]
    else:
       if my.treeVerbose:
         print(('| '*lvl) + str(len(t.rows)),t.status())
      
class Bore(Cluster):
   """
   Multi-objective clustering to find `best` rows;
   i.e. those that tend to dominate everything else.
   """
   def __init__(i, t) :
     i.rest = t.clone()
     i.best = i.div(t, 2*len(t.rows)**my.s)
   def div(i,t,lo):
     """  
     Perform a top-down recursive division 
     of data, based on their
     `y values, as follows:
    
     - Find two distant rows .
     - Check which one is best.
     - Divide the rows into those nearer `best` or `rest`
     - Add the `rest` to `i.rest`, recurse on the `best`.
     - Stop when less than `N**.s` rows.
       Return the surviving `best' ranges.
     """
     if len(t.rows) < lo: return  t
     d     = Dist(t,cols=t.cols.y)
     l,r,c = d.poles()
     xs    = [d.project(row,l,r,c) for row in t.rows]
     mid   = sum(xs) / len(xs)
     kid   = t.clone()
     if t.better(l, r):
       for x,row in zip(xs, t.rows):
         (kid if x < mid else i.rest).add(row)
     else:
       for x,row in zip(xs, t.rows):
         (kid if x >=  mid else i.rest).add(row)
     return i.div(kid,lo)
   def key(i):
     "Return the key range that most selects for best."
     best = my.e
     for  col in i.best.cols.x.values():
       all  = []
       all += [[r[col.pos], True]  for r in i.best.rows]
       all += [[r[col.pos], False] for r in i.rest.rows]
       for one in Ranges(col.txt, all).ranges:
         if one.s() > best:
           best, out = one.s(), one
     return out 

class Range(Thing):
  def __init__(i,what,xf,ranges):
    i.what,i.xf,i._ranges = what, xf, ranges
    i.n, i.yes, i.no = 0,0.0001,0.0001
    i.lo, i.hi = None, None
    i.gen=1
  def add(i,x,y):
    i.n += 1
    if y==i._ranges.goal: i.yes += 1
    else               : i.no += 1
    if i.lo is None or x < i.lo: i.lo = x
    if i.hi is None or x > i.hi: i.hi = x
  def merge(i,j):
    k     = i._ranges.bin()
    k.gen = max(i.gen,j.gen) + 1
    k.lo  = i.lo if i.lo < j.lo else j.lo
    k.hi  = i.hi if i.hi > j.hi else j.hi
    k.n   = i.n + j.n
    k.no  = i.no  + j.no
    k.yes = i.yes + j.yes
    return k
  def better(c,a,b):
    sa, sb, sc = a.s(), b.s(), c.s()
    return abs(sb - sa) < my.e or sc >= sb and sc >= sa
  def s(i):
    yes   = i.yes/i._ranges.all.yes 
    no    = i.no /i._ranges.all.no
    tmp   = yes**2/(yes+no+0.0001) 
    return tmp if tmp > my.e else 0

class Ranges(Thing):
  def __init__(i,txt,a,x=lambda z:z[0],
                       y=lambda z:z[1], goal=True):
    i.txt  = txt
    i.goal = goal
    i.bin  = lambda: Range(txt,x,i)
    i.all  = i.bin()
    i.ranges = (i.nums if Magic.nump(txt) else i.syms)(x,y,a)
  def syms(i,x,y,a):
    "When discretizing symbols, Generate one range for each symbol."
    d  = {}
    for one in a:
      x1, y1 = x(one), y(one)
      if Magic.no(x1): continue
      if not x1 in d: d[x1] = i.bin()
      d[x1].add(x1,y1)
      i.all.add(x1,y1)
    return d.values()
  def nums(i,x,y,a):
    """
    When discretizing numbers,
    Generate lots of small ranges, then
    merge those with similar scores."
    """
    return i.merge( i.grow( i.pairs(x,y,a)))
  def pairs(i,x,y,a):
    "When discretizing numbers, convert `a` into a list of x,y pairs"
    lst = [(x(z), y(z)) for z in a if not isinstance(x(z),str)]
    return sorted(lst, key= lambda z:z[0])
  def grow(i,a):
    "When discretizing numbers, divide `a` into lots of small bins."
    min  = len(a)**my.b
    use  = len(a) - min
    bins = [i.bin()]
    for j,(x,y) in enumerate(a):
      if Magic.no(x): continue
      if j < use and bins[-1].n > min:
        bins += [i.bin()]
      bins[-1].add(x,y)
      i.all.add(x,y) 
    return bins
  def merge(i,bins):
    """
    When discretizing numbers, 
    merge adjacent bins if that works better than 
    keeping them part. If any merges found, then
    recurse to merge the merged list.
    """
    j, tmp = 0, []
    while j < len(bins):
       a = bins[j]
       if j < len(bins) - 1:
          b = bins[j+1]
          c = a.merge(b)
          if c.better(a,b):
             a = c
             j += 1
       tmp += [a]
       j += 1
    return i.merge(tmp) if len(tmp) < len(bins) else bins

#--------------------------------------------------------
# Utils

def rows(x=None):
  "Read a csv file from disk."
  prep=lambda z: re.sub(r'([\n\t\r ]|#.*)','',z.strip())
  if x:
    with open(x) as f:
      for y in f: 
         z = prep(y)
         if z: yield z.split(",")
  else:
   for y in sys.stdin: 
         z = prep(y)
         if z: yield z.split(",")

def cols(src):
  "Ignore columns if, on line one, the name contains '?'."
  todo = None
  for a in src:
    todo = todo or [n for n,s in enumerate(a) if not "?"in s]
    yield [ a[n] for n in todo]

def shuffle(lst):
  "Return a shuffled list."
  random.shuffle(lst)
  return lst

def has(i,seen=None):
  """
  Report a nested object as a set of nested lists.
  If we see the same `Thing` twice, then show it the 
  first time, after which, just show its id. Do not 
  return anything that is private;
  i.e. anything whose name starts with "_".
  """
  seen = seen or {}
  if isinstance(i,Thing): 
     j =id(i) % 128021
     if i in seen: return f"#:{j}"
     seen[i]=i
     d=has(i.__dict__,seen)
     d["#"] = j
     return d
  if isinstance(i,(tuple,list)): 
     return [ has(v,seen) for v in i ]
  if isinstance(i,dict): 
     return { k:has(i[k], seen) for k in i if str(k)[0] !="_"}
  return i

def dprint(d, pre="",skip="_"):
  """
  Pretty print a dictionary, sorted by keys, ignoring 
  private slots (those that start with '_'_).
  """
  def q(z):
    if isinstance(z,float): return "%5.3f" % z
    if callable(z): return "f(%s)" % z.__name__
    return str(z)
  l = sorted([(k,d[k]) for k in d if k[0] != skip])
  return pre+'{'+", ".join([('%s=%s' % (k,q(v))) 
                             for k,v in l]) +'}'

class Test:
  """
  Unit test manager. Stores all the tests in `Test.all`. 
  Lets you list the tests, run some of them, or all.
  """
  t,f = 0,0
  all = []
  def score(s): 
    t,f = Test.t, Test.f
    return f"#TEST {s} passes = {t-f} fails = {f}"
  def go(fn=None, use=None):
    if fn:
      Test.all += [fn]
    elif use:
      [Test.run(fn) for fn in Test.all if use in fn.__name__]
    else: 
      [Test.run(fn) for fn in Test.all]
  def run(fun):    
    try:
      Test.t += 1
      print("### ",fun.__name__)
      doc = fun.__doc__ or ""
      print( "# "+ re.sub(r"\n[ ]*","\n# ",doc) )
      print("")
      random.seed(my.r)
      print(my.r, random.random())
      fun()
      print(Test.score("PASS"),':',fun.__name__)
    except Exception:
      Test.f += 1
      print(traceback.format_exc())
      print(Test.score("FAIL"),':',fun.__name__)
  def list():
    print("")
    print(__file__ + " -t [NAME]") 
    print("\nKnown test names:")
    for fun in Test.all:
      name = re.sub(r"test_","",fun.__name__)
      doc = fun.__doc__ or ""
      doc = re.sub(r"\n[ ]*","",doc)
      print(f"  {name:10s} : {doc}")
  
#----------------------------------------------
### Unit Tests
def go(fn=None,use=None):  
  """
  Decorator for test functions. 
  Adds the function to `Test.all`.
  """
  Test.go(fn=fn,use=use); return fn

@go
def test_tests():
  "List all tests."
  Test.list()

@go
def test_bye():    
  "Commit and push Github files."
  def run(s): print(s); os.system(s)
  run("git commit -am commit")
  run("git push")
  run("git status")

@go
def test_hello(): 
  "Simple test1."
  print(about()[0])

@go
def test_hetab1():
  """
  Read a small table from disk. 
  """
  t = Tab().read("../docs/data/weather4.csv")
  assert( 4 == t.cols.x[0].seen["overcast"])
  assert(14 == t.cols.x[0].n)
  assert(14 == len(t.rows))
  assert( 4 == len(t.cols.all))
  assert( 3 == len(t.cols.syms))
  print(t)

@go
def test_tab2():
  "Read a larger table from disk."
  t = Tab().read("data/auto93.csv")
  assert(398 == len(t.rows))

@go
def test_dist():
  "Check the distance calculations."
  t = Tab().read("../docs/data/auto93.csv")
  d = Dist(t)
  for r1 in shuffle(t.rows)[:10]:
    if not "?" in r1:
       assert(d.dist(r1,r1) == 0)
    n = d.neighbors(r1)
    r2 = n[ 0][1]
    r3 = n[-1][1]
    r4 = d.faraway(r1)
    print("")
    print(r1)
    print(r2, f'{d.dist(r1,r2):.3f}')
    print(r4, f'{d.dist(r1,r4):.3f}')
    print(r3, f'{d.dist(r1,r3):.3f}')
    print(*d.poles())

@go
def test_tree():
  "Recursively divide the data in two."
  t = Tab().read("../docs/data/auto93.csv")
  my.treeVerbose = True
  Tree(t,cols="y")

@go
def test_bore():
  """
  Recursively prune worst half the data 
  (down to sqrt(N) of original data).
  """
  t = Tab().read("../docs/data/auto93.csv")
  b = Bore(t)
  print([col.txt for col in t.cols.y.values()])
  print("best",b.best.status())
  print("rest",b.rest.status())
  print("all",t.status())
  print(b.key())

def _range0(xy):
  for r in Ranges("t",xy).ranges:
     print ("::",r.gen, 2**r.gen, r.lo, r.hi, r.n,r.s())


@go
def test_range1():
  "Two ranges, equal size"
  n = 10
  _range0([[i,i>n] for i in range(n*2)])

@go
def test_range2():
  "4 ranges"
  n = 10**4
  _range0( [[i, i > .1*n and i<.2*n or i>.7*n ] for i in range(n)])

@go
def test_range3():
  "5 ranges"
  n = 10**4
  _range0( [[i, i > .1*n and i<.2*n or i>.6*n and i<.7*n] for i in range(n)])

@go
def test_range4():
  "random noise: only 1 range"
  n = 10**3
  _range0( [[i, 0 if random.random() < 0.5 else 1] for i in range(n)])

@go
def test_range5():
  "random noise: only 1 range"
  n = 10**3
  _range0( [[i, 0] for i in range(n)])

@go
def test_range6():
  "3 ranges"
  n = 10**3
  _range0( [[i, i> .4*n and i < .6*n] for i in range(n)] )

@go
def test_range7():
  "singletons: 1 range"
  n = 10**2
  _range0( [[1, 0] for i in range(n)] )


#----------------------------------------------
### Main
# Start-up commands.

if __name__ == "__main__":
  my = args(help)
  if my.T: go()
  if my.t: go(use=my.t)
  if my.L: Test.list()

