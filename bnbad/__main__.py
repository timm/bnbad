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

"""
from .__init__ import *
import sys
my = args(help, __doc__)
if my.T:
  go()
  sys.exit(abs(Test.f - 1))
elif my.t:
  go(use=my.t)
else:
  my.L: Test.list()
