#!/usr/bin/env pypy3
"""
Optimizer, written as a data miner.  Break the data up into regions
of 'bad' and 'better'. Find ways to jump from 'bad' to 'better'.
Nearly all this processing takes loglinear time.

```txt
.-------.  
| Ba    | Bad <----.  planning= (better - bad)
|    56 |          |  monitor = (bad - better)
.-------.------.   |  
        | B    |   v  
        |    5 | Better  
        .------.  
```

For design details, see the "[about](about)" file.

For examples of how to use the code, see the [test functions](tests).
"""

from .lib import *
from .col import *
from .tab import *
from .my import *
from .rx import *
from .ranges import *
from .xomo import *
from .test import Test, go
from .tests import *
