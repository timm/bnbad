"""
This code predicts:

1. Time in months to complete a project (and a month is 152 hours of
work and includes all management support tasks associated with the coding).
2. The risk associated with the current project decisions.
   This [risk model](cocrisk) is calculated from a set of rules that add a "risk value" for
every "bad smell" within the current project settings.

The standard COCOMO effort model assumes that:
-  Effort is exponential on size of code
- Within the exponent there are set of scale factors that increase effort exponentially
- Outside the exponent there are set of effort multipliers that change effort in a linear manner
  - either linearly increasing  or linearly decreasing.

This code extends the standard COCOMO effort model as follows:
- This code comes with a set of mitigations that might improve a project.
  It is a sample manner:
  - To loop over all those mitigations, trying each for a particular project. 
  - Define and test your own mitigations.
- Many of the internal parameters of COCOMO are not known with any certainty.
  -  So this model represents all such internals as a range of options.
  - By running this estimated, say, 1000 times, you can get an estimate of the range of possible values.

## Attributes

This code also for the easy extension of the model.  If you think
that other factors do (or do not) influence effort in an exponential
or liner manner, then it is simple to extend this code with your
preferred set of attributes.

### Scale Factors
if _more_ then exponential _more_ effort i

|What| Notes|
|----|------|
| Flex | development flexibility|
|Arch| architecture or risk resolution |
|Pmat| process maturity |
|Prec| precedentedness|
|Team|team cohesion|

### Positive Effort Multipliers
If more, then linearly more effort 

|What| Notes|
|----|------|
|cplx | product complexity|
|data| database size (DB bytes/SLOC) |
|docu| documentation|
|pvol| platform volatility (frequency of major changes/ frequency of minor changes )|
|rely| required reliability |
|ruse |required reuse|
|stor| required % of available RAM
|time |required % of available CPU

### Negative Effort Multipliers
If more, then linearly more effort 


|What| Notes|
|----|------|
|acap|analyst capability|
|aexp|applications experience |
|ltex| language and tool-set experience |
|pcap |programmer capability|
|pcon| personnel continuity (% turnover per year) |
|plex| platform experience|
|sced| dictated development schedule|
|site| multi-site development|
|tool| use of software tools|

(For guidance on how to score projects on these scales, see tables 11,12,13,etc
of the [Cocomo manual](http://sunset.usc.edu/csse/affiliate/private/COCOMOII_2000/COCOMOII-040600/modelman.pdf).)

```py
## Code
### Imports
import bnbad
from lib import Thing,o
from copy import deepcopy as kopy
from x import F,I
from cocrisk import rules

### Class Cocomo
class Cocomo(Thing):
  __name__ = "Cocomo"
```
Here's where we defined attributes to be floats _F_ or integers _I_.
```py
  defaults = o(
      misc= o( kloc = F(2,1000),
               a    = F(2.2,9.8),
               goal = F(0.1, 2)),
      pos = o( rely = I(1,5),  data = I(2,5), cplx = I(1,6),
               ruse = I(2,6),  docu = I(1,5), time = I(3,6),
               stor = I(3,6),  pvol = I(2,5)),
      neg = o( acap = I(1,5),  pcap = I(1,5), pcon = I(1,5),
               aexp = I(1,5),  plex = I(1,5), ltex = I(1,5),
               tool = I(1,5),  site = I(1,6), sced = I(1,5)),
      sf  = o( prec = I(1,6),  flex = I(1,6), arch = I(1,6),
               team = I(1,6),  pmat = I(1,6)))
```
This code initializes the parameters then overrides then with values
in `listofdicts` (if any are supplied).

```py
  def __init__(i,listofdicts=[]):
    i.x, i.y, dd = o(), o(), kopy(Cocomo.defaults)
    # set up the defaults
    for d in dd:
      for k in dd[d] : i.x[k]  = dd[d][k] # can't +=: no background info
    # apply any other constraints
    for dict1 in listofdicts:
      for k in dict1 :
         try: i.x[k] += dict1[k] # now you can +=
         except Exception as e:
              print(k, e)
    # ----------------------------------------------------------
    for k in dd.misc:i.y[k]= i.x[k]()
    for k in dd.pos: i.y[k]= F( .073,  .21)()   * (i.x[k]() -3) +1
    for k in dd.neg: i.y[k]= F(-.178, -.078)()  * (i.x[k]() -3) +1
    for k in dd.sf : i.y[k]= F(-1.56, -1.014)() * (i.x[k]() -6)
    # ----------------------------------------------------------
```
Effort model:
```py
  def effort(i):
    em, sf = 1, 0
    b      = (0.85-1.1)/(9.18-2.2) * i.x.a() + 1.1+(1.1-0.8)*.5
    for k in Cocomo.defaults.sf  : sf += i.y[k]
    for k in Cocomo.defaults.pos : em *= i.y[k]
    for k in Cocomo.defaults.neg : em *= i.y[k]
    return round(i.x.a() * em * (i.x.goal()*i.x.kloc()) ** (b + 0.01*sf), 1)
```
Risk model:
```py
  def risk(i, r=0):
    for k1,rules1 in rules.items():
      for k2,m in rules1.items():
        x  = i.x[k1]()
        y  = i.x[k2]()
        z  = m[x-1][y-1]
        r += z
    return round(100 * r / 104, 1)
```
### Risk Model
See [the risk model](cocrisk).

### Project mitations
See the _better_ variable within the [COCOMO examples file](cocoeg).

For an example on how to use it, see the _one_ function of [cocomook](cocomook).
