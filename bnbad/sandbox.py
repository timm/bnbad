"""
Place for experiments: best to ignore this.
"""

no = lambda z: z is "?"
yes = lambda z: z isnt "?"
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


class Num:
  def __init__(i, pos=0, txt=""):
    i.n, i.pos, i.txt = 0, pos, txt
    i.mu, i.lo, i.hi = 0, 10**32, -10**32

  def __add__(i, x):
    if yes(x):
      i.n += 1
      i.mu += (x-i.mu)/i.n
      i.lo = min(i.lo, x)
      i.hi = max(i.hi, x)


class Tab:
  def __init__(i, a):
    i.x, i.y, i.all, i.rows = [], [], [], []
    for pos, txt in enumerate(a):
      one = (Num if nump(txt) else Sym)(pos, txt)
      i.all.append(one)
      (i.y if goalp(x) else i.x).append(one)

  def __add__(i, lst):
    i.all += [Row(i, lst)]


class Row:
  def __init__(i, tab, cells):
    i.cells = cells
    i.ranges = cells[:]
    i.tab = tab
    for col, cell in zip(tab.cols, about):
       col + cell


class Bin:
  def __init__(i, klass=Num):
    i.klass = klass


class Bins:
  def __init__(i, a, x=first, y=last, klassx=Num, klassy=Num):
    i.all =
  n = len(a)/16
  out = [Bin(
  for, he=
