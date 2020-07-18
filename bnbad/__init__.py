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

import os
#import random,math,sys,re,os
#from copy   import deepcopy as kopy
from .lib    import *
from .col    import *
from .tab    import *
from .my     import *
from .rx     import *
from .ranges import *
from .xomo   import *
from .test   import *

@go
def test_tests():
  "List all tests."
  Test.list()

@go
def test_fail():
  "Test the test engine with one failure"
  assert(0)

@go
def test_bye():    
  "Commit and push Github files."
  def run(s): print(s); assert( 0 == os.system(s))
  run("git commit -am commit")
  run("git push")
  run("git status")

@go
def test_hetab1():
  "Read a small table from disk."
  import data
  t = Tab().read(data.weather4)
  assert( 4 == t.cols.x[0].seen["overcast"])
  assert(14 == t.cols.x[0].n)
  assert(14 == len(t.rows))
  assert( 4 == len(t.cols.all))
  assert( 3 == len(t.cols.syms))

@go
def test_tab2():
  "Read a larger table from disk."
  import data
  t = Tab().read(data.auto93)
  assert(398 == len(t.rows))

@go
def test_dist():
  "Check the distance calculations."
  import data
  t = Tab().read(data.auto93)
  d = Dist(t)
  for r1 in shuffle(t.rows)[:10]:
    if not "?" in r1:
       assert(d.dist(r1,r1) == 0)
    n = d.neighbors(r1)
    r2 = n[ 0][1]
    r3 = n[-1][1]
    r4 = d.faraway(r1)
    d1=d.dist(r1,r2)
    d2= d.dist(r1,r4)
    d3= d.dist(r1,r3)
    assert(d1 <= d2 <= d3)
    assert(0.2 <= d2 <=d3)
    assert(len(d.poles())==3)

@go
def test_tree():
  "Recursively divide the data in two."
  from .auto93 import data
  t = Tab().read(data)
  my.treeVerbose = True
  t=Tree(t,cols="y")
  assert(15 == len(t.leaves))
   

@go
def test_bore():
  """\
  Recursively prune worst half the data.
  """
  import data
  t = Tab().read(data.auto93)
  b = Bore(t)
  print([col.txt for col in t.cols.y.values()])
  print("best",b.best.status())
  print("rest",b.rest.status())
  print("all",t.status())
  k = b.key()
  assert(k.s() > 0.69)
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
                      x1 = [ 0.34, 0.49 ,0.51, 0.6]*n,
                      x2 = [0.6  ,0.7 , 0.8 , 0.89]*n,
                      x3 = [0.13 ,0.23, 0.33 , 0.35]*n,
                      x4 = [0.6  ,0.7,  0.8 , 0.9]*n,
                      x5 = [0.1  ,0.2,  0.3 , 0.4]*n),
               width= 20, verbose=False,
               show = "%.2f",
               chops= [.25,  .5, .75],
               marks= ["-", "-", " "])
  all = [x for g in groups for x in g.parts]
  assert(len(all) == 5)
  assert(len(groups) == 3)
  for n,one in enumerate(all):
    assert(len(one.all) == 1024)
    if n > 0:
        assert(one.med >= all[n-1].med)
        assert(one.rank >= all[n-1].rank)
