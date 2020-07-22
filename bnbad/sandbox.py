"""
Place for experiments: best to ignore this.
"""
import random

r = random.random
no = lambda z: z is "?"
yes = lambda z: not no(z)
ako = lambda y, z: isinstance(y, z)
strp = lambda z: ako(z, str)
nump = lambda z: "<" in s or "$" in s or ">" in s
last = lambda z: z[-1]
first = lambda z: z[0]
lessp = lambda z: "<" in s
goalp = lambda z: "<" in s or "!" in s or ">" in s
klassp = lambda z: "!" in s


class Sym:
  def __init__(i, pos=0, txt=""):
    i.n, i.pos, i.txt = 0, pos, txt
    i.seen = {}
    i.mode, i.most = None, 0

  def __add__(i, x):
    if yes(x):
      i.n += 1
      tmp = i.seen[x] = i.seen.get(x, 0) + 1
      if tmp > i.most:
         i.most, i.mode = tmp, x
    return i

  def dist(i, x, y):
    return 1 if no(x) and no(y) else x isnt y

  def merge(i, x, y, wx=1, wy=1):
    if no(x) or no(y): return "?"
    elif r() < wx/(wx+wy): return x
    else: return y


class Num:
  def __init__(i, pos=0, txt=""):
    i.n, i.pos, i.txt = 0, pos, txt
    i.mu, i.lo, i.hi = 0, 10**32, -10**32
    i.w = -1 if lessp(txt) else 1

  def __add__(i, x):
    if yes(x):
      i.n += 1
      i.mu += (x-i.mu)/i.n
      i.lo = min(i.lo, x)
      i.hi = max(i.hi, x)
    return i

  def norm(i, x):
    return x if no(x) else (x - i.lo) / (i.hi - i.lo + 0.000001)

  def dist(i, x, y):
    if no(x) and no(y):
      return 1
    if no(x):
      x = i.lo if y > i.mu else i.hi
    if no(y):
      y = i.lo if x > i.mu else i.hi
    return abs(i.norm(x) - i.norm(y))

  def merge(i, x, y, wx=1, wy=1):
    return "?" if no(x) or no(y) else (x*wx + y*wy) / (wx+wy)


class Tab:
  def __init__(i, a):
    i.x, i.y, i.all, i.rows = [], [], [], []
    i.Klass = None
    for pos, txt in enumerate(a):
      one = (Num if nump(txt) else Sym)(pos, txt)
      i.all.append(one)
      (i.y if goalp(x) else i.x).append(one)
      if klassp(txt);
        i.Klass = one

  def add(i, x, keep=True):
    x = [Row(i, x.cells if isa(x, Row) else x)]
    if keep:
        i.all += [x]


class MiniK:
  def __init__(i, t, m=20, k=32):
    i.c = []
    i.n = 0

  def __add__(i, row):
    t.add(row, keep=False)
    i.n += 1
    if len(i.c) < i.k:
       row.neighbors = []
       i.c += [raw]
    else:
       c1 = sorted([(c1.dist(row), c1) for c1 in i.c],
                    keyword=first)[0][1]
       c1.w += 1
       c1.neighbors += [row]
     if i.n % i.m is 0:
       for c1 in i.c:
         i.adjust(c1)
   def adjust(i,c):
     for row in c.neighbors.
       for col in t.tab.x:
         p = col.pos
         c.cells[p] = col.merge(c.cells[p], row.cells[p], c.w)
     c1.neighbors = []


class Row:
  def __init__(i, tab, cells):
    i.w = 0
    i.cells = cells
    i.ranges = cells[:]
    i.tab = tab
    [col + cell for col, cell in zip(tab.cols, about)]

  def __mul__(i, j):
    k = i.cells[:]
    for col in i.tab.y: k[col.pos] = None
    for col for col in i.tab.x:
      p = col.pos
      k[p] = col.merge(i.cells[p], j.cells[p), i.w, j.w)

  def dist(i, j)
    d = 0
    for col in i.tab.x:
      inc = col.dist(i.cells[col.pos], j.cells[col.pos])
      d += inc**2
    return (d/len(i.tab.x))**0.5


class Bin:
  def __init__(i, klass=Num):
    i.klass = klass


class Bins:
  def __init__(i, a, x=first, y=last, klassx=Num, klassy=Num):
    i.all =
  n = len(a)/16
  out = [Bin(
  for, he=
