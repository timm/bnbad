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

Do you want to make your software more ethical?  BnBAD is a
collection of data structures that support ethical the kind of
ethical reasoning listed above.  It is a multi-objective optimizer
that reasons by breaking up problems into regions of `bad` and
`better`, then looks for ways on how to jump between those regions.

BnBAD might be an ethical choice in domains:

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
  [Zitler's continuous domination predicate](#bnbad.Tab.better)
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
           Bore       :has 1 :to 2 :of Tab
           Tree       :has 1 :to * :of Tab
        Col(txt,pos)
           Num(mu,lo,hi)
           Sym(mode)
        Cols          :has 1 :to * :of Col
        Dist          :has 1 :to 1 :of Tab
        Range(lo,hi)
        Ranges        :has 1 :to * :of Range
        Tab(rows)     :has 1 :to 1 :of Cols  
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
from copy import deepcopy as kopy

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
    h("decision list: minimum leaf size",               M= 10),
    h("decision list: maximum height",                   H= 4),
    h("decision list: ratio of negative examples",     N= 4),
    h("coefficient for distance" ,                      p= 2),
    h("random number seed" ,                            r = 1),
    h("tree leaves must be at least n**s in size" ,     s= 0.5),
    h("stats: Cliff's Delta 'dull'",                    Sdull=[.147,.33,.474]),
    h("stats: Coehn 'd'",                               Scohen=0.2),
    h("stats: number of boostrap samples",              Sb=500),
    h("stats: bootstrap confidences",                   Sconf=0.01),
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
     best  = my.e
     bests = i.best.rows
     rests = i.rest.rows
     rests = shuffle(rests)[ :my.N*len(bests) ]
     for  col in i.best.cols.x.values():
       all  = []
       all += [[r[col.pos], True]  for r in bests]
       all += [[r[col.pos], False] for r in rests]
       for one in Ranges(col.txt, all,
                         get = col.pos).ranges:
         if one.s() > best:
           best, out = one.s(), one
     return out 

class DecisionList(Thing):
  def __init__(i, t, lvl=my.H):
    i.t=t
    i.leaf = None
    if lvl > 0 and len(t.rows) >= my.M: 
      b = Bore(t)
      i.split = b.key()
      i.col = i.split._ranges.get
      i.leaf, kid = t.clone(), t.clone()
      for row in t.rows:
        (i.leaf if i.split.matches(row) else kid).add(row)
      i.kid = DecisionList(kid, lvl-1)
  def show(i,pre="  "): 
    if i.leaf:
      print(pre+"if", i.split._ranges.txt," in ",i.split.lo, "..",i.split.hi,
           "then",  i.leaf.status(), len(i.leaf.rows))
      i.kid.show(pre="el")
    else:
     print("else", i.t.status(), len(i.t.rows))

class Range(Thing):
  def __init__(i,what,ranges):
    i.what,i._ranges = what,  ranges
    i.n, i.yes, i.no = 0,0.0001,0.0001
    i.lo, i.hi = None, None
    i.gen=1
  def matches(i, row):
    v = row[i._ranges.get]
    return v != "?" and i.lo <= v and v <= i.hi
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
  """
  Report how to divide a list of pairs `[x,y]` 
  such that groups of `x` values most select for some
  desired `y` (which is called the `goal`.
  """
  def __init__(i,txt,a,goal=True, get=lambda z:z[0]):
    i.txt  = txt
    i.goal = goal
    i.get  = get
    i.bin  = lambda: Range(txt,i)
    i.all  = i.bin()
    i.ranges = (i.nums if Magic.nump(txt) else i.syms)(a)
  def syms(i,a):
    "When discretizing symbols, Generate one range for each symbol."
    d  = {}
    for x1,y1 in a:
      if Magic.no(x1): continue
      if not x1 in d: d[x1] = i.bin()
      d[x1].add(x1,y1)
      i.all.add(x1,y1)
    return d.values()
  def nums(i,a):
    """
    When discretizing numbers,
    Generate lots of small ranges, then
    merge those with similar scores."
    """
    return i.merge( i.grow( i.pairs(a)))
  def pairs(i,a):
    "When discretizing numbers, convert `a` into a list of x,y pairs"
    lst = [(x,y) for x,y in a if not Magic.no(x)]
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

def pairs(lst):
  "Return the i-th and i+1-th item in a list."
  last=lst[0]
  for i in lst[1:]:
    yield last,i
    last = i

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

def perc(a,p=[.25,.5,.75]):
  ls = sprted(a)
  return [ l[int(p0 * len(a))] for p0 in p ]

def xtile(lst,lo=0,hi=1,
             width = 50,
             chops = [0.1 ,0.3,0.5,0.7,0.9],
             marks = [" " ,".","."," "," "],
             bar   = "",
             star  = "o",
             show  = " %5.3f"):
    """
    Pretty print a large list of numbers.
    Take a list of numbers, sort them,
    then print them as a
    horizontal
    xtile chart (in ascii format). The default is a
    contracted _quintile_ that shows the
    10,30,50,70,90 breaks in the data (but this can be
    changed- see the optional flags of the function).
    """
    def at(p): 
      return ordered[int(len(lst)*p)]
    def norm(x): 
      return int(width*float((x - lo))/(hi - lo+0.00001))
    def pretty(lst):
      return ', '.join([show % x for x in lst])
    ordered = sorted(lst)
    what    = [at(p)   for p in chops]
    where   = [norm(n) for n in  what]
    out     = [" "] * width
    marks1 = marks[:]
    for one,two in pairs(where):
      for i in range(one,two):
        out[i] = marks1[0]
      marks1 = marks1[1:]
    if bar:  out[int(width/2)]  = bar
    if star: out[norm(at(0.5))] = star
    return ''.join(out) +  "," +  pretty(what)
 
def rxs(d, width = 50,
           show  = "%5.0f",
           chops = [0.1 ,0.3,0.5,0.7,0.9],
           marks = [" " ,".",".","."," "]):
  """
  Manager for a set of treatment results.
  Given a dictionary of values, sort the values by their median
  then iteratively merge together adjacent similar items.
  """
  def merge(lst, lvl=0):
    """
    Do one pass, see what we can combine.
    If nothing, then print  `lst`. Else, recurse.
    """
    j,tmp = 0,[]
    while j < len(lst):
       x = lst[j]
       if j < len(lst) - 1: 
         y = lst[j+1]
         if abs(x.med - y.med) <= tiny or x == y:
           tmp += [x+y] # merge x and y
           j   += 2
           continue
       tmp += [x]
       j   += 1
    if len(tmp) < len(lst):
       return merge(tmp, lvl+1) 
    else:
       for n,group in enumerate(lst):
         for rx in group.parts:
           rx.rank = n
           print(n, rx) 
       return lst
  #-------------------------------
  p    = lambda n: a[ int( n*len(a) )]
  a    = sorted([x for k in d for x in d[k]])
  tiny = (p(.9) - p(.2))/2.56 * my.Scohen
  return merge(sorted([Rx(rx    = k,    all = d[k], 
                          lo    = a[0], hi  = a[-1],
                          show  = show,
                          width = width,
                          chops = chops,
                          marks = marks) 
                    for k in d]))

 
class Rx(Thing):
  """
  A treatment "`Rx`" is a label (`i.rx`) and a set of 
  values (`i.all`).  
  
  Similar treatments can be grouped together
  by the [`rxs`](#bnbad.rxs) function
  into sets of values with the same `rank`
  Things in the same rank are statistically 
  indistinguishable, as judged by all three of:

  1. A very fast non-parametric `D` test 
      - Sort the numns, ignore divisions less that
        30% of "spread" (90th-10th percentile range); 
  2. A (slightly more thorough) non-parametric effect 
     size test (the Cliff's Delta);
      -  Two lists are different if, usually, 
         things from one list do not fall into the middle 
         of the other.
  3. (very thorough) non-parametric 
     significance test (the Bootstrap);
      - See if hundreds of sample-with-replacements
        sets from two lists and  different properties to 
        the overall list.
  
  Of the above, the third is far slower than the rest. Often, if it is
  omitted, the results are often the same as just using 1+2.  So when
  each treatment has 1000s of values, it would be reasonable to skip
  it. Without bootstrapping,  256 treatments with 1000 values
  can be sorted in less than 2 seconds. But with that skipping
  that same process takes half an hour.
  """
  def __init__(i, rx="", all=[], lo=0,hi=1,  
                         width = 50,
                         show  = "%5.0f",
                         chops = [0.1 ,0.3,0.5,0.7,0.9],
                         marks = [" " ,"-"," ","-"," "]):
    i.rx   = rx
    i.all  = sorted([x for x in all if x != "?"])
    i.lo   = min(i.all[0],lo)
    i.hi   = max(i.all[-1],hi)
    i.n    = len(i.all)
    i.med  = i.all[int(i.n/2)]
    i.parts= [i]
    i.rank = 0
    i.width,i.chops,i.marks,i.show = width,chops,marks,show
  def __lt__(i,j): 
    "Treatments are sorted on their `med` value."
    return i.med < j.med
  def __eq__(i,j):
    """
    Two treatments are statistically indistinguishable
    if a non-parametric effect size test (`cliffsDelta`)
    and a non-parametric significance test (`bootstrap`)
    say that there are no differences between them.
    """
    return i.cliffsDelta(j) and  i.bootstrap(j)
  def __add__(i,j):
    "Treatments can be combined"
    k =  Rx(all = i.all + j.all,
                  lo  = min(i.lo, j.lo), 
                  hi  = max(i.hi, j.hi))
    k.parts = i.parts + j.parts
    return k
  def __repr__(i):
    "Treatments can be printed."
    return '%10s %s' % (i.rx, xtile(i.all, i.lo, i.hi,
                                    show = i.show,
                                    width = i.width,
                                    chops = i.chops,
                                    marks = i.marks))

  def cliffsDelta(i,j, dull=my.Sdull):
    """
    For every item in `lst1`, find its position in `lst2` Two lists are
    different if, usually, things from one list do not fall into the
    middle of the other.
  
    This code employees a few tricks to make all this run fast (e..g
    pre-sort the lists, work over `runs` of same values).
    """
    def runs(lst):
      for j,two in enumerate(lst):
        if j == 0: one,i = two,0
        if one!=two:
          yield j - i,one
          i = j
        one=two
      yield j - i + 1,two
    # --- end runs function ---------------------
    lst1, lst2 = i.all, j.all
    m, n = len(lst1), len(lst2)
    lst2 = sorted(lst2)
    j = more = less = 0
    for repeats,x in runs(sorted(lst1)):
      while j <= (n - 1) and lst2[j] <  x: j += 1
      more += j*repeats
      while j <= (n - 1) and lst2[j] == x: j += 1
      less += (n - j)*repeats
    d= (more - less) / (m*n)
    return abs(d)  <= dull
  
  def bootstrap(i,j,onf=my.Sconf,b=my.Sb):
    """
    Two  lists y0,z0 are the same if the same patterns can be seen in
    all of them, as well as in 100s to 1000s  sub-samples from each.
    From p220 to 223 of the Efron text  'introduction to the bootstrap'.
    
    This function checks for  different properties between (a) the two
    lists and (b) hundreds of sample-with-replacements sets.
    """
    class Sum(): 
      "# Quick & dirty class to summarize sets of values."
      def __init__(i,some=[]):
        i.sum = i.n = i.mu = 0 ; i.all=[]
        for one in some: i.put(one)
      def put(i,x):
        i.all.append(x);
        i.sum +=x; i.n += 1; i.mu = float(i.sum)/i.n
      def __add__(i1,i2): return Sum(i1.all + i2.all)
    def testStatistic(y,z):
       "Define the property that we will check for."
       tmp1 = tmp2 = 0
       for y1 in y.all: tmp1 += (y1 - y.mu)**2
       for z1 in z.all: tmp2 += (z1 - z.mu)**2
       s1    = float(tmp1)/(y.n - 1)
       s2    = float(tmp2)/(z.n - 1)
       delta = z.mu - y.mu
       if s1+s2:
         delta =  delta/((s1/y.n + s2/z.n)**0.5)
       return delta
    def one(lst): 
      "Sampling with replacement."
      return lst[ int(random.uniform(0,len(lst))) ]
    #--------------
    y0, z0 = i.all, j.all
    y,z  = Sum(y0), Sum(z0)
    x    = y + z
    baseline = testStatistic(y,z)
    yhat = [y1 - y.mu + x.mu for y1 in y.all]
    zhat = [z1 - z.mu + x.mu for z1 in z.all]
    bigger = 0
    for i in range(b):
      if testStatistic(Sum([one(yhat) for _ in yhat]),
                       Sum([one(zhat) for _ in zhat])) > baseline:
        bigger += 1
    return bigger / b >= conf

class X(Thing):
  """
  Class for holding knowledge about some variable `X`. 
  Instances of this class:

  - Know their `lo` and `hi` value;
  - Know that if `hi` is missing, to just use `lo`;
  - Know how to calculate a value within a legal range.
  - Know how to cache that value (so we can use it over and over again)
  - Know how to check new values
  - Know how to combine themselves 
  """
  def __init__(i, lo,hi=None): 
    i.lo = lo
    i.hi = lo if hi==None else hi
    i.lo0, i.hi0 = i.lo, i.hi
    i.x  = None
  def ok(i,z): 
    return i.lo0 <= z <= i.hi0
  def __call__(i):
    if i.x == None: i.x = i.get()
    return i.x
  def __iadd__(i,j): 
    lo = j.lo
    hi = j.lo if j.hi==None else j.hi
    if i.ok(lo) and i.ok(hi):
      i.lo, i.hi, i.x  = lo, hi, None
      return i
    raise IndexError('out of bounds %s %s' % (lo, hi))

class F(X): 
  "Floats"
  def get(i): return random.uniform(i.lo, i.hi)

class I(X): 
  "Integers"
  def get(i): return random.randint(i.lo, i.hi)

class Cocomo(Thing):
  """
  This code predicts:
  
  1. Time in months to complete a project (and a month is 152 hours of
  work and includes all management support tasks associated with the coding).
  2. The risk associated with the current project decisions.
     This [risk model](cocrisk) is calculated from a set of rules that add a "risk value" for
  every "bad smell" within the current project settings.
  
  The standard COCOMO effort model assumes that:
  -  Effort is exponential on size of code
  - Within the exponent there are set of scale factors that increase effort exponentially
  - Outside the exponent there are set of effort multipliers that change effort in a linear manner
    - either linearly increasing  or linearly decreasing.
  
  This code extends the standard COCOMO effort model as follows:
  - This code comes with a set of mitigations that might improve a project.
    It is a sample manner:
    - To loop over all those mitigations, trying each for a particular project. 
    - Define and test your own mitigations.
  - Many of the internal parameters of COCOMO are not known with any certainty.
    -  So this model represents all such internals as a range of options.
    - By running this estimated, say, 1000 times, you can get an estimate of the range of possible values.
  
  ## Attributes
  
  This code also for the easy extension of the model.  If you think
  that other factors do (or do not) influence effort in an exponential
  or liner manner, then it is simple to extend this code with your
  preferred set of attributes.
  
  ### Scale Factors
  if _more_ then exponential _more_ effort i
  
  |What| Notes|
  |----|------|
  | Flex | development flexibility|
  |Arch| architecture or risk resolution |
  |Pmat| process maturity |
  |Prec| precedentedness|
  |Team|team cohesion|
  
  ### Positive Effort Multipliers
  If more, then linearly more effort 
  
  |What| Notes|
  |----|------|
  |cplx | product complexity|
  |data| database size (DB bytes/SLOC) |
  |docu| documentation|
  |pvol| platform volatility (frequency of major changes/ frequency of minor changes )|
  |rely| required reliability |
  |ruse |required reuse|
  |stor| required % of available RAM
  |time |required % of available CPU
  
  ### Negative Effort Multipliers
  If more, then linearly more effort 
  
  
  |What| Notes|
  |----|------|
  |acap|analyst capability|
  |aexp|applications experience |
  |ltex| language and tool-set experience |
  |pcap |programmer capability|
  |pcon| personnel continuity (% turnover per year) |
  |plex| platform experience|
  |sced| dictated development schedule|
  |site| multi-site development|
  |tool| use of software tools|
  
  (For guidance on how to score projects on these scales, see tables 11,12,13,etc
  of the [Cocomo manual](http://sunset.usc.edu/csse/affiliate/private/COCOMOII_2000/COCOMOII-040600/modelman.pdf).)
  """
  defaults = o(
      misc= o( kloc = F(2,1000),
               a    = F(2.2,9.8),
               goal = F(0.1, 2)),
      pos = o( rely = I(1,5),  data = I(2,5), cplx = I(1,6),
               ruse = I(2,6),  docu = I(1,5), time = I(3,6),
               stor = I(3,6),  pvol = I(2,5)),
      neg = o( acap = I(1,5),  pcap = I(1,5), pcon = I(1,5),
               aexp = I(1,5),  plex = I(1,5), ltex = I(1,5),
               tool = I(1,5),  site = I(1,6), sced = I(1,5)),
      sf  = o( prec = I(1,6),  flex = I(1,6), arch = I(1,6),
               team = I(1,6),  pmat = I(1,6)))

  better = o(
    none    = o( goal=F(1)),
    people  = o( goal=F(1),   acap=I(5), pcap=I(5),  pcon=I(5),
                 aexp=I(5),   plex=I(5), ltex=I(5)),
    tools   = o( goal=F(1),
                 time=I(3),   stor=I(3), pvol=I(2),
                 tool=I(5),   site=I(6)),
    precFlex= o( goal=F(1),
                 time=I(5),   flex=I(5)),
    archResl= o( goal=F(1),
                 arch=I(5)),
    slower  = o( goal=F(1),
                 sced=I(5)),
    process = o( goal=F(1),
                 pmat=I(5)),
    less    = o( goal=F(0.5), data=I(2)),
    team    = o( goal=F(1),
                 team=I(5)),
    worst   = o( goal=F(1),
                 rely=I(1),   docu=I(5), 
                 time=I(3),   cplx=I(3)))

  projects = o(
    osp    = o(goal= F(1),
                prec=I(1,2),    flex=I(2,5), arch=I(1,3),
                team=I(2,3),    pmat=I(1,4), stor=I(3,5),
                ruse=I(2,4),    docu=I(2,4), acap=I(2,3),
                pcon=I(2,3),    aexp=I(2,3), ltex=I(2,4),
                tool=I(2,3),    sced=I(1,3), cplx=I(5,6),
                kloc=F(75,125), data=I(3),   pvol=I(2), rely=I(5),
                pcap=I(3),      plex=I(3),   site=I(3)),
    osp2   = o(goal=F(1),     prec=I(3,5), pmat=I(4,5), docu=I(3,4), 
                ltex=I(2,5), sced=I(2,4), kloc=F(75,125),
                flex=I(3),   arch=I(4),   team=I(3), time=I(3), stor=I(3),
                data=I(4),   pvol=I(3),   ruse=I(4), rely=I(5), acap=I(4), 
                pcap=I(3),   pcon=I(3),   aexp=I(4), plex=I(4), tool=I(5), 
                cplx=I(4),   site=I(6)),
    flight = o(goal=F(1),
                rely=I(3,5), data=I(2,3),
                cplx=I(3,6), time=I(3,4),
                stor=I(3,4), acap=I(3,5),
                aexp=I(2,5), pcap=I(3,5),
                plex=I(1,4), ltex=I(1,4),
                tool=I(2),   sced=I(3),
                pmat=I(2,3), kloc=F(7,418)),
    ground = o(  goal=F(1),
                tool=I(2),   sced=I(3),
                rely=I(1,4), data=I(2,3), cplx=I(1,4),
                time=I(3,4), stor=I(3,4), acap=I(3,5),
                aexp=I(2,5), pcap=I(3,5), plex=I(1,4),
                ltex=I(1,4), pmat=I(2,3), kloc=F(11,392)))

  def __init__(i,listofdicts=[]):
    i.x, i.y, dd = o(), o(), kopy(Cocomo.defaults)
    # set up the defaults
    for d in dd:
      for k in dd[d] : i.x[k]  = dd[d][k] # can't +=: no background info
    # apply any other constraints
    for dict1 in listofdicts:
      for k in dict1 :
         try: i.x[k] += dict1[k] # now you can +=
         except Exception as e:
              print(k, e)
    # ----------------------------------------------------------
    for k in dd.misc:i.y[k]= i.x[k]()
    for k in dd.pos: i.y[k]= F( .073,  .21)()   * (i.x[k]() -3) +1
    for k in dd.neg: i.y[k]= F(-.178, -.078)()  * (i.x[k]() -3) +1
    for k in dd.sf : i.y[k]= F(-1.56, -1.014)() * (i.x[k]() -6)
    # ----------------------------------------------------------
  def effort(i):
    em, sf = 1, 0
    b      = (0.85-1.1)/(9.18-2.2) * i.x.a() + 1.1+(1.1-0.8)*.5
    for k in Cocomo.defaults.sf  : sf += i.y[k]
    for k in Cocomo.defaults.pos : em *= i.y[k]
    for k in Cocomo.defaults.neg : em *= i.y[k]
    return round(i.x.a() * em * (i.x.goal()*i.x.kloc()) ** (b + 0.01*sf), 1)
  def risk(i, r=0):
    for k1,rules1 in rules.items():
      for k2,m in rules1.items():
        x  = i.x[k1]()
        y  = i.x[k2]()
        z  = m[x-1][y-1]
        r += z
    return round(100 * r / 104, 1)
  def rules(i):
    _ = 0
    ne=   [      [_,_,_,1,2,_], # bad if lohi 
                 [_,_,_,_,1,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_]]
    nw=  [       [2,1,_,_,_,_], # bad if lolo 
                 [1,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_]]
    nw4= [       [4,2,1,_,_,_], # very bad if  lolo 
                 [2,1,_,_,_,_],
                 [1,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_]]
    sw4= [       [_,_,_,_,_,_], # very bad if  hilo 
                 [_,_,_,_,_,_],
                 [1,_,_,_,_,_],
                 [2,1,_,_,_,_],
                 [4,2,1,_,_,_],
                 [_,_,_,_,_,_]]
    
    # bounded by 1..6
    ne46= [      [_,_,_,1,2,4], # very bad if lohi
                 [_,_,_,_,1,2],
                 [_,_,_,_,_,1],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_]]
    sw=   [      [_,_,_,_,_,_], # bad if hilo
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [1,_,_,_,_,_],
                 [2,1,_,_,_,_]]
    sw26= [      [_,_,_,_,_,_], # bad if hilo
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [1,_,_,_,_,_],
                 [2,1,_,_,_,_]]
    sw46= [      [_,_,_,_,_,_], # very bad if hilo
                 [_,_,_,_,_,_],
                 [_,_,_,_,_,_],
                 [1,_,_,_,_,_],
                 [2,1,_,_,_,_],
                 [4,2,1,_,_,_]]
    
    return dict( 
      cplx= dict(acap=sw46, pcap=sw46, tool=sw46), #12
      ltex= dict(pcap=nw4),  # 4
      pmat= dict(acap=nw,   pcap=sw46), # 6
      pvol= dict(plex=sw), #2
      rely= dict(acap=sw4,  pcap=sw4,  pmat=sw4), # 12
      ruse= dict(aexp=sw46, ltex=sw46),  #8
      sced= dict(
        cplx=ne46, time=ne46, pcap=nw4, aexp=nw4, acap=nw4,  
        plex=nw4, ltex=nw,  pmat=nw, rely=ne, pvol=ne, tool=nw), # 34
      stor= dict(acap=sw46, pcap=sw46), #8
      team= dict(aexp=nw,   sced=nw,   site=nw), #6
      time= dict(acap=sw46, pcap=sw46, tool=sw26), #10
      tool= dict(acap=nw,   pcap=nw,   pmat=nw)) # 6
    

 
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
  t = Tab().read("bnbad/ata/weather4.csv")
  assert( 4 == t.cols.x[0].seen["overcast"])
  assert(14 == t.cols.x[0].n)
  assert(14 == len(t.rows))
  assert( 4 == len(t.cols.all))
  assert( 3 == len(t.cols.syms))
  print(t)

@go
def test_tab2():
  "Read a larger table from disk."
  t = Tab().read("bnbad/data/auto93.csv")
  assert(398 == len(t.rows))

@go
def test_dist():
  "Check the distance calculations."
  t = Tab().read("data/auto93.csv")
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
  t = Tab().read("data/auto93.csv")
  my.treeVerbose = True
  Tree(t,cols="y")

@go
def test_bore():
  """
  Recursively prune worst half the data 
  (down to sqrt(N) of original data).
  """
  t = Tab().read("data/auto93.csv")
  b = Bore(t)
  print([col.txt for col in t.cols.y.values()])
  print("best",b.best.status())
  print("rest",b.rest.status())
  print("all",t.status())
  k = b.key()
  print("SCORE",k._ranges.txt,k.s()) #print("KEY",b.key())
  for _ in range(1):
     DecisionList(t).show()

def _range0(xy):
  "Worker for the tests"
  for r in Ranges("$t",xy).ranges:
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

@go
def test_rxs():
    """
    This demo groups and ranks five treatments
    `x1,x2,x3,x4,x5`:
    We will find these treatments divide into three  groups (`0,1,2`):
  
    0  x5 (   ----o---                   ), 0.200,  0.300,  0.400
    0  x3 (    ----o                     ), 0.230,  0.330,  0.350
    1  x1 (              -o--            ), 0.490,  0.510,  0.600
    2  x2 (                      ----o-- ), 0.700,  0.800,  0.890
    2  x4 (                      ----o-- ), 0.700,  0.800,  0.900
    """
    n = 256
    rxs(    
        dict(
               x1 = [ 0.34, 0.49 ,0.51, 0.6]*n,
               x2 = [0.6  ,0.7 , 0.8 , 0.89]*n,
               x3 = [0.13 ,0.23, 0.33 , 0.35]*n,
               x4 = [0.6  ,0.7,  0.8 , 0.9]*n,
               x5 = [0.1  ,0.2,  0.3 , 0.4]*n),
        width= 30,
        show = "%.2f",
        chops= [.25,  .5, .75],
        marks= ["-", "-", " "])
  
#----------------------------------------------
### Main
# Start-up commands.

if __name__ == "__main__":
  my = args(help)
  if my.T: go()
  if my.t: go(use=my.t)
  if my.L: Test.list()

