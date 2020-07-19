from .lib import *
from .my  import *
from .col import *
from .ranges import *
import math

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
  def __init__(i,t, cols=my.c):
    i.lo     = 2*len(t.rows)**my.s
    i.leaves = []
    i.dist   = Dist(t, cols = t.cols.__dict__[cols])
    i.root   = TreeNode(t,None,i,lvl=0)
    for j in i.leaves:
      dom = 0
      js = j.t.mid()
      for k in i.leaves:
        if id(j) != id(k):
          ks = k.t.mid()
          dom += t.better(js, ks)
      j.dom = dom
  def show(i): 
    "Show the tree."
    print(', '.join([c.txt for c in i.root.t.cols.y.values()]))
    print(i.root.t.status())
    i.root.show("")          
  def bore(i):
    "Return the best leaf and some of the rest."
    i.leaves = sorted(i.leaves, key=lambda z: z.dom)
    best = i.leaves[0].t
    rest = []
    for leaf in i.leaves[1:]:
      rest += leaf.t.rows
    rest = shuffle(rest)[ :len(best.rows)*my.N ]
    return best, i.root.t.clone(rows)
  def key(i):
    "Return the key range that most selects for best."
    best = my.e 
    bests,rests = i.bore()
    for  col in best.cols.x.values():
      all  = []
      all += [[row[col.pos], True]  for row in bests]
      all += [[row[col.pos], False] for row in rests]
      for one in Ranges(col.txt, all,
                        get = col.pos).ranges:
        if one.s() > best:
          best, out = one.s(), one
    return out 

class TreeNode:
  def __init__(i, t, _up, _root, lvl): 
    i.t       = t
    i._up     = _up       
    i.kids    = []
    i._root   = _root
    i.l, i.r  = None, None
    i.c, i.mid, i.dom = 0, 0, 0
    if len(t.rows) < _root.lo:
       i._root.leaves += [i]
       i.id = len(i._root.leaves) - 1
    else:
      d  = i._root.dist
      i.l,i.r,i.c = d.poles()
      xs     = [d.project(r,i.l,i.r,i.c) for r in t.rows]
      i.mid  = sum(xs) / len(xs)
      tables = [t.clone(), t.clone()]
      for x,r in zip(xs, t.rows):
        tables[x >= i.mid].add(r) 
      if len(tables[0].rows) < len(t.rows) and \
         len(tables[1].rows) < len(t.rows) :
         for t1 in tables:
           i.kids += [TreeNode(t1, i, _root, lvl+1)]
  def show(i,pre):
    s = f"{pre}{len(i.t.rows)}"
    if i.kids:
      print(s)
    else:
      stars = "*"*int(10*i.dom/len(i._root.leaves))
      dom   = int(100*i.dom/len(i._root.leaves))
      print(f"{s} [{i.id}] {i.t.status()}{stars} {dom} %")
    for kid in  i.kids: kid.show(pre + "|  ")

class DecisionList(Thing):
  def show(i): i.root.show(i,"") 
  def __init__(i, t,_up=None, lvl=my.H):
    i.t, i._up, i.leaf = t, _up,  None
    if lvl > 0 and len(t.rows) >= my.M: 
      i.split = Tree(t).key()
      i.col   = i.split._ranges.get
      i.leaf, kid = t.clone(), t.clone()
      for row in t.rows:
        (i.leaf if i.split.matches(row) else kid).add(row)
      i.kid = DecisionList(kid, up,  lvl-1)
  def show(i,pre):
    if i.leaf:
      print( pre+"if", i.split._ranges.txt," in ",
             i.split.lo, "..",i.split.hi,
             "then",  i.leaf.status(), i.dom )
      i.kid.show(pre=pre + "|  ")
    else:
     print("else", i.t.status(), i.dom)

 
