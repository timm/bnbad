"""
Tools to generate `Num`ber and `Sym`bolic columns,
generate summaries of data in columns, and to manage
sets of columns (`Cols`).
"""
from .lib import Thing


class Magic:
  """
  Define magic characterss.
  Used in column headers to denote goals, klasses, numbers.
  Used also to denote things to skip (columns, specific cells).
  """
  def no(s):
    "Things to skip."
    return s == "?"

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


class Col(Thing):
  def __init__(i, pos, txt):
    i.n, i.pos, i.txt = 0, pos, txt
    i.w = -1 if Magic.lessp(txt) else 1

  def __add__(i, x):
    if Magic.no(x):
      return x
    i.n += 1
    return i.add(x)


class Num(Col):
  def __init__(i, *lst):
    super().__init__(*lst)
    i.mu, i.lo, i.hi = 0, 10**32, -10**32

  def mid(i): return i.mu

  def add(i, x):
    x = float(x)
    i.lo, i.hi = min(i.lo, x), max(i.hi, x)
    i.mu = i.mu + (x - i.mu)/i.n
    return x

  def norm(i, x):
    if Magic.no(x):
      return x
    return (x - i.lo) / (i.hi - i.lo + 0.000001)

  def dist(i, x, y):
    if Magic.no(x) and Magic.no(y):
      return 1
    if Magic.no(x):
      x = i.lo if y > i.mu else i.hi
    if Magic.no(y):
      y = i.lo if x > i.mu else i.hi
    return abs(i.norm(x) - i.norm(y))


class Sym(Col):
  def __init__(i, *lst):
    super().__init__(*lst)
    i.seen, i.most, i.mode = {}, 0, None

  def mid(i): return i.mode

  def add(i, x):
    tmp = i.seen[x] = i.seen.get(x, 0) + 1
    if tmp > i.most:
      i.most, i.mode = tmp, x
    return x

  def dist(i, x, y):
    return 1 if Magic.no(x) and Magic.no(y) else x != y


class Cols(Thing):
  def __init__(i):
    i.x, i.y, i.nums, i.syms, i.all, i.klas = {}, {}, {}, {}, [], None

  def add(i, lst):
    [col.add(lst[col.pos]) for col in i.all]

  def klass(i, lst):
    return lst[i.klas]

  def header(i, lst):
    for pos, txt in enumerate(lst):
      tmp = (Num if Magic.nump(txt) else Sym)(pos, txt)
      i.all += [tmp]
      (i.y if Magic.goalp(txt) else i.x)[pos] = tmp
      (i.nums if Magic.nump(txt) else i.syms)[pos] = tmp
      if Magic.klassp(txt):
        i.klas = tmp
