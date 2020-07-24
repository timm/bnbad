"""
Place for experiments: best to ignore this.
"""
import re
import sys
import pprint
import random
from .data import auto93


def r(): return random.random()
def no(z): return z == "?"
def yes(z): return not no(z)
def isa(y, z): return isinstance(y, z)
def strp(z): return isa(z, str)
def nump(z): return "<" in z or "$" in z or ">" in z
def last(z): return z[-1]
def first(z): return z[0]
def lessp(z): return "<" in z
def goalp(z): return "<" in z or "!" in z or ">" in z
def klassp(z): return "!" in z
def shuffle(z): random.shuffle(z); return z


def rows(x=None, f=sys.stdin):
  """
  Read csv rows from stdio or a file or a string or a list.
  Kill any whitespace or comments.
  """
  def strings(z):
    for y in z.splitlines():
      yield y

  def csv(z):
    with open(z) as fp:
      for y in fp:
        yield y

  if x:
    f = csv if x[-3:] == 'csv' else strings
  for y in f(x):
    y = re.sub(r'([\n\t\r ]|#.*)', '', y.strip())
    if y:
      yield y.strip().split(",")


def cols(src):
  "Skip columns whose names contain '?'"
  todo = None
  for a in src:
    todo = todo or [n for n, s in enumerate(a) if "?" not in s]
    yield [a[n] for n in todo]


def prep(src):
  "Compile a column appropriately, skipping col1"
  prep = []
  def num(z): return z if no(z) else float(z)
  def noop(z): return z
  for a in src:
    if prep:
      yield [f(x) for x, f in zip(a, prep)]
    else:
      prep = [(num if nump(x) else noop) for x in a]
      yield a


class Any:
  "Classes that can pretty print themselves."
  def __repr__(i):
    def d(x, xs=None, use=lambda z: str(z)[0] != "_"):
      "Converts `x` into a nested dictionary."
      if isa(x, (tuple, list)):
        return [d(v, xs) for v in x]
      elif isa(x, dict):
        return {k: d(x[k], xs) for k in x if use(k)}
      elif not isa(x, Any):
        return x
      else:
        xs = xs or {}
        j = id(x) % 128021  # show ids succinctly
        if x in xs:
          return f"#:{j}"
        xs[x] = x
        y = d(x.__dict__, xs)
        y["#"] = j
        return y
    return pprint.pformat(d(i.__dict__), compact=True)


class Bins(Any):
  min = .05

  class Num(Any):
    def __init__(i, all, pos=0, txt="", lo=0, hi=None):
      i.txt, i.pos = pos, txt
      i._all, i.lo, i.hi = all, lo, hi if hi else len(a)

    def per(i, p=0.5):
      j = int(len(i._all) * (lo + (hi - lo) * p))
      return i._all.a[j].cells[i.pos]

    def sd(i): return (i.per(.75) - i.per(.25)) / 2.54

    def merge(i, j):
      return Bins.Num(all=i._all, pos=i.pos, txt=i.txt,
                      lo=min(i.lo, j.lo), hi=max(i.hi, j.hi))

    def val(i, z): return z.cells[i.pos]

  def __init__(i, a, want=True, x=0, y=1):
    i.x, i.y, i.want = x, y, want
    i.all = i.bin()
    tmp = [z for z in a if yes(z.cells[i.x])]
    i.a = sorted(tmp, key=lambda z: z.cells[i.x])
    i.bins = i.shrink(i.grow([i.bin()]))

  def bin(i): return o(x=Bins.Num(pos=i.x), y=Sym(pos=i.y))

  def grow(i, bins):
    for n, z in enumerate(i.a):
      if bins[-1].x.n > len(i.a) / 16:
        bins += [i.bin()]
      i.add(bins[-1], n)
      i.add(i.all, n)
    i.bins = i.merge(bins)

  def shrink(i, bins):
    tmp = []
    for j in len(bins):
      a = bins[j]
      if j < len(bins) - 2:
        b = bins[j + 1]
        c = i.merge(a, b)
        if i.better(c, a, b):
          a = c
          j += 1
      tmp += [a]
      j += 1
    return tmp if len(tmp) == len(bins) else i.shrink(tmp)

  def add(i, r, n):
    r.x.add(n)
    r.y.add(r.y.val(n) == i.want)

  def better(i, c, a, b):
    a, b, c = i.score(a), i.score(b), i.score(c)
    return abs(b - a) < Bins.min or c >= b and c >= a

  def merge(i, r, s):
    return i.make(y=r.y + s.y, n=r.n + s.n,
                  lo=min(r.lo, s.lo),
                  hi=max(r.hi, s.hi))

  def score(i, r, p=10**-9):
    y = r.y / (p + i.all.y)
    n = r.n / (p + i.all.n)
    return 0 if y < n * (1 + Bins.min) else y * y / (p + y + n)


class Sym(Any):
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

  def val(i, row): return row.cells[i.pos]

  def merge(i, j):
    k = Sym(i.pos, i.txt)
    k.n = i.n + j.n
    for x in i.seen:
      k.seen[x] = i.seen[x]
    for x in j.seen:
      k.seen[x] = k.seen.get(x, 0) + j.seen[x]
    for x in k.seen:
      if k.seen[x] > k.most:
        k.most = k.seen[x]
        k.mode = x


class Num(Any):
  def __init__(i, pos=0, txt=""):
    i.n, i.pos, i.txt = 0, pos, txt
    i.mu, i.lo, i.hi = 0, 10**32, -10**32
    i.w = -1 if lessp(txt) else 1

  def __add__(i, x):
    if yes(x):
      i.n += 1
      i.mu += (x - i.mu) / i.n
      i.lo = min(i.lo, x)
      i.hi = max(i.hi, x)
    return i

  def val(i, row): return row.cells[i.pos]


class Tab(Any):
  def __init__(i, src=None):
    i.x, i.y, i.cols, i.rows = [], [], [], []
    i.theKlass = None
    i.read(src)

  def read(i, src=None):
    if src:
      [i.add(a) for a in prep(cols(rows(src)))]

  def add(i, a):
    i.row(a) if i.cols else i.head(a)

  def head(i, a):
    for pos, txt in enumerate(a):
      one = (Num if nump(txt) else Sym)(pos, txt)
      i.cols.append(one)
      (i.y if goalp(txt) else i.x).append(one)
      if klassp(txt):
        i.theKlass = one

  def row(i, x):
    x = x.cells if isa(x, Row) else x
    [col + cell for col, cell in zip(i.cols, x)]
    i.rows += [x]


class Row(Any):
  def __init__(i, tab, cells):
    i.cells = cells
    i.ranges = cells[:]
    i._tab = tab


class Tests:
  def all():
    for x in dir(Tests):
      if "test_" in x:
        getattr(Tests, x)()

  def test_tab():
    t = Tab(data.auto93)
    print(t.y[0])


Tests.all()
