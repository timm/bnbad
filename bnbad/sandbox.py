"""
Place for experiments: best to ignore this.
"""
import re
import sys
import pprint
import random
import data


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
  def make(i):
     return o(lo=10**32, hi=-10**32, y=0, n=0, all=i)

  def __init__(i, a, want=True, x=first, y=last):
    i.a = []
    i.want = want
    i.all = i.make()
    for z in a:
      if yes(x(z)):
        i.add(i.all, x(z), y(z))
        i.all += [z]]

  def add(i, r, x, y):
    r.x += y == i.want
    r.y += y != i.want
    r.lo= min(r.lo, x)
    r.hi= max(r.hi, x)

  def merge(i, r, s):
    t= i.make()
    t.y = r.y + s.y
    t.n = r.n + s.n
    t.lo = min(r.lo, s.lo)
    t.hi = max(r.hi, s.hi)
    return t

  def sd(i, lo=0, hi=None):
    if hi is None:
      hi= len(i.a)
    hi1= i.x(a[int(lo + (hi - lo)*0.9)])
    lo1= i.x(a[int(lo + (hi - lo)*0.1)])
    return (hi1 - lo1) / 2.54

  def split(i):
    n= class NSBins(Any):

  def __init__(i, want):
    i.want= want
    i.bins= NSBin(i)


class NSBin(Any):
  def __init__(i, bins):
    i.bins= bins
    i.lo= 10**32
    i.hi= -1 * i.lo
    i.y= i.n = 0

  def add(i, num, sym):
    if yes(num):
      i.lo= min(i.lo, num)
      i.hi= max(i.hi, num)
      i.y += sym == i.bins.want
      i.n += sym != i.bins.want

  def score(i):
    p= 10**-9
    y= i.y / (p + i.bins.y)
    n= i.n / (p + i.bins.n)
    return 0 if y < n + 0.05 else y*y / (p+y+n)

  def merge(i, j):
    k= NSBin(i.bins)
    k.lo= min(i.lo, j.lo)
    k.hi= max(i.hi, j.hi)
    k.y= i.y + j.y
    k.n= i.n + j.n
    return k


class Sym(Any):
  def __init__(i, pos=0, txt=""):
    i.n, i.pos, i.txt= 0, pos, txt
    i.seen= {}
    i.mode, i.most= None, 0

  def __add__(i, x):
    if yes(x):
      i.n += 1
      tmp= i.seen[x] = i.seen.get(x, 0) + 1
      if tmp > i.most:
        i.most, i.mode= tmp, x
    return i

  def dist(i, x, y):
    return 1 if no(x) and no(y) else x != y


class Num(Any):
  def __init__(i, pos=0, txt=""):
    i.n, i.pos, i.txt= 0, pos, txt
    i.mu, i.lo, i.hi= 0, 10**32, -10**32
    i.w= -1 if lessp(txt) else 1

  def __add__(i, x):
    if yes(x):
      i.n += 1
      i.mu += (x-i.mu)/i.n
      i.lo= min(i.lo, x)
      i.hi= max(i.hi, x)
    return i


class Tab(Any):
  def __init__(i, src=None):
    i.x, i.y, i.cols, i.rows= [], [], [], []
    i.theKlass= None
    i.read(src)

  def read(i, src=None):
    if src:
      [i.add(a) for a in prep(cols(rows(src)))]

  def add(i, a):
    i.row(a) if i.cols else i.head(a)

  def head(i, a):
    for pos, txt in enumerate(a):
      one= (Num if nump(txt) else Sym)(pos, txt)
      i.cols.append(one)
      (i.y if goalp(txt) else i.x).append(one)
      if klassp(txt):
        i.theKlass= one

  def row(i, x):
    x= x.cells if isa(x, Row) else x
    [col + cell for col, cell in zip(i.cols, x)]
    i.rows += [x]


class Row(Any):
  def __init__(i, tab, cells):
    i.cells= cells
    i.ranges = cells[: ]
    i._tab= tab


class Tests:
  def all():
    for x in dir(Tests):
      if "test_" in x:
        getattr(Tests, x)()

  def test_tab():
    t= Tab(data.auto93)
    print(t.y[0])


Tests.all()
