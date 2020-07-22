"""
Divide data into ranges, then merge
similar values.
"""

from .col import Magic
from .my import my
from .lib import *
from .lib import Thing


class Ranges(Thing):
  """
  Report how to divide a list of pairs `[x,y]`
  such that groups of `x` values most select for some
  desired `y` (which is called the `goal`.
  """
  def __init__(i, txt, a, goal=True, get=lambda z: z[0]):
    i.txt = txt
    i.goal = goal
    i.get = get
    i.bin = lambda: Range(txt, i)
    i.all = i.bin()
    i.ranges = (i.nums if Magic.nump(txt) else i.syms)(a)

  def syms(i, a):
    "When discretizing symbols, Generate one range for each symbol."
    d = {}
    for x1, y1 in a:
      if Magic.no(x1):
        continue
      if x1 not in d:
        d[x1] = i.bin()
      d[x1].add(x1, y1)
      i.all.add(x1, y1)
    return d.values()

  def nums(i, a):
    """
    When discretizing numbers,
    Generate lots of small ranges, then
    merge those with similar scores."
    """
    return i.merge(i.grow(i.pairs(a)))

  def pairs(i, a):
    "When discretizing numbers, convert `a` into a list of x,y pairs"
    lst = [(x, y) for x, y in a if not Magic.no(x)]
    return sorted(lst, key=lambda z: z[0])

  def grow(i, a):
    "When discretizing numbers, divide `a` into lots of small bins."
    min = len(a)**my.b
    use = len(a) - min
    bins = [i.bin()]
    for j, (x, y) in enumerate(a):
      if Magic.no(x):
        continue
      if j < use and bins[-1].n > min:
        bins += [i.bin()]
      bins[-1].add(x, y)
      i.all.add(x, y)
    return bins

  def merge(i, bins):
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
        if c.better(a, b):
          a = c
          j += 1
      tmp += [a]
      j += 1
    return i.merge(tmp) if len(tmp) < len(bins) else bins


class Range(Thing):
  def __init__(i, what, ranges):
    i.what, i._ranges = what,  ranges
    i.n, i.yes, i.no = 0, 0.0001, 0.0001
    i.lo, i.hi = None, None
    i.gen = 1

  def matches(i, row):
    v = row[i._ranges.get]
    return v != "?" and i.lo <= v and v <= i.hi

  def add(i, x, y):
    i.n += 1
    if y == i._ranges.goal:
      i.yes += 1
    else:
      i.no += 1
    if i.lo is None or x < i.lo:
      i.lo = x
    if i.hi is None or x > i.hi:
      i.hi = x

  def merge(i, j):
    k = i._ranges.bin()
    k.gen = max(i.gen, j.gen) + 1
    k.lo = i.lo if i.lo < j.lo else j.lo
    k.hi = i.hi if i.hi > j.hi else j.hi
    k.n = i.n + j.n
    k.no = i.no + j.no
    k.yes = i.yes + j.yes
    return k

  def better(c, a, b):
    sa, sb, sc = a.s(), b.s(), c.s()
    return abs(sb - sa) < my.e or sc >= sb and sc >= sa

  def s(i):
    yes = i.yes/i._ranges.all.yes
    no = i.no / i._ranges.all.no
    tmp = yes**2/(yes+no+0.0001)
    return tmp if tmp > my.e else 0
