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
"""
from .__init__ import *
my = args(help,__doc__)
if   my.T : go()
elif my.t : go(use=my.t)
else      : my.L: Test.list()
