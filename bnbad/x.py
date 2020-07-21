from .lib import *


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
  def __init__(i, lo, hi=None):
    i.lo = lo
    i.hi = lo if hi == None else hi
    i.lo0, i.hi0 = i.lo, i.hi
    i.x = None

  def ok(i, z):
    return i.lo0 <= z <= i.hi0

  def __call__(i):
    if i.x == None:
      i.x = i.get()
    return i.x

  def __iadd__(i, j):
    lo = j.lo
    hi = j.lo if j.hi == None else j.hi
    if i.ok(lo) and i.ok(hi):
      i.lo, i.hi, i.x = lo, hi, None
      return i
    raise IndexError('out of bounds %s %s' % (lo, hi))


class F(X):
  "Floats"
  def get(i): return random.uniform(i.lo, i.hi)


class I(X):
  "Integers"
  def get(i): return random.randint(i.lo, i.hi)
