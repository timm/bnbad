"""
Test cases, specific for this system.
"""

from .lib import *
from .col import *
from .tab import *
from .my import *
from .rx import *
from .ranges import *
from .xomo import *
from .test import Test, go


@go
def test_tests():
  "List all tests."
  Test.list()


@go
def test_fail():
  "Test the test engine with one failure"
  assert(0)


@go
def test_hetab1():
  "Read a small table from disk."
  from .data import weather4
  t = Tab().read(weather4)
  assert(4 == t.cols.x[0].seen["overcast"])
  assert(14 == t.cols.x[0].n)
  assert(14 == len(t.rows))
  assert(4 == len(t.cols.all))
  assert(3 == len(t.cols.syms))


@go
def test_tab2():
  "Read a larger table from disk."
  from .data import auto93
  t = Tab().read(auto93)
  assert(398 == len(t.rows))


@go
def test_dist():
  "Check the distance calculations."
  from .data import auto93
  t = Tab().read(auto93)
  d = Dist(t)
  for r1 in shuffle(t.rows)[:10]:
    if not "?" in r1:
      assert(d.dist(r1, r1) == 0)
    n = d.neighbors(r1)
    r2 = n[0][1]
    r3 = n[-1][1]
    r4 = d.faraway(r1)
    d1 = d.dist(r1, r2)
    d2 = d.dist(r1, r4)
    d3 = d.dist(r1, r3)
    assert(d1 <= d2 <= d3)
    assert(0.2 <= d2 <= d3)
    assert(len(d.poles()) == 3)


@go
def test_tree():
  """\
  Recursively divide the data in two.

  When working on `auto93`, the goals are

      ['<weight', '>acceleration', '>!mpg']

  which to say, minimize `weight`, maximize `acceleration` and
  `mpg`.  If you call this after setting `my.treeVerbose=True` then
  this tree will get printed. Note the leaf four lines from the
  bottom, marked with "`*`".  This is cluster is "best" (least
  `weight`, most `acceleration`, most `mph`).

         398
         | 211
         | | 57
         | | | 30 {4526.53, 13.65, 10.33}
         | | | 27 {4094.56, 11.41, 11.11}
         | | 154
         | | | 65
         | | | | 32 {3482.34, 13.34, 20.00}
         | | | | 33 {4022.91, 14.76, 20.00}
         | | | 89
         | | | | 47
         | | | | | 26 {2893.35, 15.22, 20.00}
         | | | | | 21 {2591.00, 14.82, 20.00}
         | | | | 42
         | | | | | 25 {3158.60, 16.80, 20.00}
         | | | | | 17 {3396.71, 19.74, 20.00}
         | 187
         | | 104
         | | | 86
         | | | | 48
         | | | | | 23 {2230.26, 16.53, 30.00}
         | | | | 38 {2428.71, 19.29, 30.00}
         | | | 18 {2289.94, 17.08, 20.00}
         | | 83
       * | | | 35 {1982.63, 17.23, 39.43} 
         | | | 48
         | | | | 21 {2308.19, 13.83, 31.43}
         | | | | 27 {2069.67, 15.44, 30.37}

  """
  from .data import auto93
  t = Tab().read(auto93)
  my.treeVerbose = True
  t = Tree(t, cols="y")
  assert(15 == len(t.leaves))
  t.show()


@go
def test_bore():
  """\
  Recursively prune worst half the data.

   When working on `auto93`, the goals are

      ['<weight', '>acceleration', '>!mpg']

  then this finds a `best` cluster of

       {2492.5, 19.7, 34.1}

  A random sample of the remaining data is then
  collected into `rest` which has median goal
  scores of:

      {3012.2, 15.2, 22.9}

  Then we run a rule learner that generates a decision
  list that seperates `best` from `rest`.

      if   $displacement  in   68 .. 105 then {2055.9, 16.9, 32.1} 
      elif $displacement  in  107 .. 140 then {2533.1, 15.9, 26.6} 
      elif $displacement  in  141 .. 200 then {2910.2, 16.2, 24.2} 
      elif $horsepower    in   72 .. 139 then {3437.2, 16.3, 19.9} 
      else {4201.2, 12.5, 14.2} 

  """
  verbose = True
  from .data import auto93
  t = Tab().read(auto93)
  best, rest, worst = Tree(t).bore()
  if verbose:  # my.V:
    print([col.txt for col in t.cols.y.values()])
    print("all", t.status())
    print("best", best.status())
    print("rest", rest.status())
  midBest = best.mid()
  midRest = rest.mid()
  assert(t.better(midBest, midRest))
  d1 = DecisionList(best, rest)
  d1.show()
  d2 = DecisionList(worst, best)
  d2.show()
  return True
  k = b.key()
  assert(k.s() > 0.69)
  d = DecisionList(t)
  assert(5 == len(d.leaves))
  if False:  # my.V:
    for _ in range(1):
      d.show()


def _range0(n, xy):
  "Worker for the tests"
  verbose = False
  assert(n == len(Ranges("$t", xy).ranges))
  if verbose:
    for r in Ranges("$t", xy).ranges:
      print("::", r.gen, 2**r.gen, r.lo, r.hi, r.n, r.s())


@go
def test_range1():
  "Two ranges, equal size"
  n = 10
  _range0(2, [[i, i > n] for i in range(n*2)])


@go
def test_range2():
  "4 ranges"
  n = 10**4
  _range0(4, [[i, i > .1*n and i < .2*n or i > .7*n]
              for i in range(n)])


@go
def test_range3():
  "5 ranges"
  n = 10**4
  _range0(5, [[i, i > .1*n and i < .2*n or i > .6*n and i < .7*n]
              for i in range(n)])


@go
def test_range4():
  "random noise: only 1 range"
  n = 10**3
  _range0(1, [[i, 0 if random.random() < 0.5 else 1]
              for i in range(n)])


@go
def test_range5():
  "random noise: only 1 range"
  n = 10**3
  _range0(1, [[i, 0] for i in range(n)])


@go
def test_range6():
  "3 ranges"
  n = 10**3
  _range0(3, [[i, i > .4*n and i < .6*n] for i in range(n)])


@go
def test_range7():
  "singletons: 1 range"
  n = 10**2
  _range0(1, [[1, 0] for i in range(n)])


@go
def test_rxs():
  """\
  Group and ranks five treatments.

  We will find these treatments divide into three  groups (`0,1,2`):

       0,       x5,   --o--             ,0.20, 0.30, 0.40
       0,       x3,    --o              ,0.23, 0.33, 0.35
       1,       x1,          -o-        ,0.49, 0.51, 0.60
       2,       x2,               ---o- ,0.70, 0.80, 0.89
       2,       x4,               ---o- ,0.70, 0.80, 0.90

  """
  n = 256
  groups = rxs(dict(
      x1=[0.34, 0.49, 0.51, 0.6]*n,
      x2=[0.6, 0.7, 0.8, 0.89]*n,
      x3=[0.13, 0.23, 0.33, 0.35]*n,
      x4=[0.6, 0.7,  0.8, 0.9]*n,
      x5=[0.1, 0.2,  0.3, 0.4]*n),
      width=20, verbose=False,
      show="%.2f",
      chops=[.25,  .5, .75],
      marks=["-", "-", " "])
  all = [x for g in groups for x in g.parts]
  assert(len(all) == 5)
  assert(len(groups) == 3)
  for n, one in enumerate(all):
    assert(len(one.all) == 1024)
    if n > 0:
      assert(one.med >= all[n-1].med)
      assert(one.rank >= all[n-1].rank)
