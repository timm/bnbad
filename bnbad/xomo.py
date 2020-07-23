"""
This code predicts:

1. Time in months to complete a project (and a month is 152 hours of
work and includes all management support tasks associated with the coding).
2. The risk associated with the current project decisions.
   This [risk model](cocrisk) is calculated from a set of rule
   that add a "risk value" for
every "bad smell" within the current project settings.

The standard COCOMO effort model assumes that:
-  Effort is exponential on size of code
- Within the exponent there are set of scale factors that
  increase effort exponentially
- Outside the exponent there are set of effort multipliers
  that change effort in a linear manner
  - either linearly increasing  or linearly decreasing.

This code extends the standard COCOMO effort model as follows:
- This code comes with a set of mitigations that might improve a project.
  It is a sample manner:
  - To loop over all those mitigations, trying each for a particular project.
  - Define and test your own mitigations.
- Many of the internal parameters of COCOMO are not known with any certainty.
  -  So this model represents all such internals as a range of options.
  - By running this estimated, say, 1000 times,
    you can get an estimate of the range of possible values.

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
"""
from .lib import o,  Thing
from .x import F, I
from copy import deepcopy as kopy

defaults = o(
    misc=o(kloc=F(2, 1000),
           a=F(2.2, 9.8),
           goal=F(0.1, 2)),
    pos=o(rely=I(1, 5),  data=I(2, 5), cplx=I(1, 6),
          ruse=I(2, 6),  docu=I(1, 5), time=I(3, 6),
          stor=I(3, 6),  pvol=I(2, 5)),
    neg=o(acap=I(1, 5),  pcap=I(1, 5), pcon=I(1, 5),
          aexp=I(1, 5),  plex=I(1, 5), ltex=I(1, 5),
          tool=I(1, 5),  site=I(1, 6), sced=I(1, 5)),
    sf=o(prec=I(1, 6),  flex=I(1, 6), arch=I(1, 6),
         team=I(1, 6),  pmat=I(1, 6)))

better = o(
    none=o(goal=F(1)),
    people=o(goal=F(1),   acap=I(5), pcap=I(5),  pcon=I(5),
             aexp=I(5),   plex=I(5), ltex=I(5)),
    tools=o(goal=F(1),
            time=I(3),   stor=I(3), pvol=I(2),
            tool=I(5),   site=I(6)),
    precFlex=o(goal=F(1),
               time=I(5),   flex=I(5)),
    archResl=o(goal=F(1),
               arch=I(5)),
    slower=o(goal=F(1),
             sced=I(5)),
    process=o(goal=F(1),
              pmat=I(5)),
    less=o(goal=F(0.5), data=I(2)),
    team=o(goal=F(1),
           team=I(5)),
    worst=o(goal=F(1),
            rely=I(1),   docu=I(5),
            time=I(3),   cplx=I(3)))

projects = o(
    osp=o(goal=F(1),
          prec=I(1, 2),    flex=I(2, 5), arch=I(1, 3),
          team=I(2, 3),    pmat=I(1, 4), stor=I(3, 5),
          ruse=I(2, 4),    docu=I(2, 4), acap=I(2, 3),
          pcon=I(2, 3),    aexp=I(2, 3), ltex=I(2, 4),
          tool=I(2, 3),    sced=I(1, 3), cplx=I(5, 6),
          kloc=F(75, 125), data=I(3),   pvol=I(2), rely=I(5),
          pcap=I(3),      plex=I(3),   site=I(3)),
    osp2=o(goal=F(1),     prec=I(3, 5), pmat=I(4, 5), docu=I(3, 4),
           ltex=I(2, 5), sced=I(2, 4), kloc=F(75, 125),
           flex=I(3),   arch=I(4),   team=I(3), time=I(3), stor=I(3),
           data=I(4),   pvol=I(3),   ruse=I(4), rely=I(5), acap=I(4),
           pcap=I(3),   pcon=I(3),   aexp=I(4), plex=I(4), tool=I(5),
           cplx=I(4),   site=I(6)),
    flight=o(goal=F(1),
             rely=I(3, 5), data=I(2, 3),
             cplx=I(3, 6), time=I(3, 4),
             stor=I(3, 4), acap=I(3, 5),
             aexp=I(2, 5), pcap=I(3, 5),
             plex=I(1, 4), ltex=I(1, 4),
             tool=I(2),   sced=I(3),
             pmat=I(2, 3), kloc=F(7, 418)),
    ground=o(goal=F(1),
             tool=I(2),   sced=I(3),
             rely=I(1, 4), data=I(2, 3), cplx=I(1, 4),
             time=I(3, 4), stor=I(3, 4), acap=I(3, 5),
             aexp=I(2, 5), pcap=I(3, 5), plex=I(1, 4),
             ltex=I(1, 4), pmat=I(2, 3), kloc=F(11, 392)))
_ = 0
ne = [[_, _, _, 1, 2, _],  # bad if lohi
      [_, _, _, _, 1, _],
      [_, _, _, _, _, _],
      [_, _, _, _, _, _],
      [_, _, _, _, _, _],
      [_, _, _, _, _, _]]
nw = [[2, 1, _, _, _, _],  # bad if lolo
      [1, _, _, _, _, _],
      [_, _, _, _, _, _],
      [_, _, _, _, _, _],
      [_, _, _, _, _, _],
      [_, _, _, _, _, _]]
nw4 = [[4, 2, 1, _, _, _],  # very bad if  lolo
       [2, 1, _, _, _, _],
       [1, _, _, _, _, _],
       [_, _, _, _, _, _],
       [_, _, _, _, _, _],
       [_, _, _, _, _, _]]
sw4 = [[_, _, _, _, _, _],  # very bad if  hilo
       [_, _, _, _, _, _],
       [1, _, _, _, _, _],
       [2, 1, _, _, _, _],
       [4, 2, 1, _, _, _],
       [_, _, _, _, _, _]]

# bounded by 1..6
ne46 = [[_, _, _, 1, 2, 4],  # very bad if lohi
        [_, _, _, _, 1, 2],
        [_, _, _, _, _, 1],
        [_, _, _, _, _, _],
        [_, _, _, _, _, _],
        [_, _, _, _, _, _]]
sw = [[_, _, _, _, _, _],  # bad if hilo
      [_, _, _, _, _, _],
      [_, _, _, _, _, _],
      [1, _, _, _, _, _],
      [2, 1, _, _, _, _]]
sw26 = [[_, _, _, _, _, _],  # bad if hilo
        [_, _, _, _, _, _],
        [_, _, _, _, _, _],
        [_, _, _, _, _, _],
        [1, _, _, _, _, _],
        [2, 1, _, _, _, _]]
sw46 = [[_, _, _, _, _, _],  # very bad if hilo
        [_, _, _, _, _, _],
        [_, _, _, _, _, _],
        [1, _, _, _, _, _],
        [2, 1, _, _, _, _],
        [4, 2, 1, _, _, _]]

rules = dict(
    cplx=dict(acap=sw46, pcap=sw46, tool=sw46),  # 12
    ltex=dict(pcap=nw4),  # 4
    pmat=dict(acap=nw,   pcap=sw46),  # 6
    pvol=dict(plex=sw),  # 2
    rely=dict(acap=sw4,  pcap=sw4,  pmat=sw4),  # 12
    ruse=dict(aexp=sw46, ltex=sw46),  # 8
    sced=dict(
        cplx=ne46, time=ne46, pcap=nw4, aexp=nw4, acap=nw4,
        plex=nw4, ltex=nw,  pmat=nw, rely=ne, pvol=ne, tool=nw),  # 34
    stor=dict(acap=sw46, pcap=sw46),  # 8
    team=dict(aexp=nw,   sced=nw,   site=nw),  # 6
    time=dict(acap=sw46, pcap=sw46, tool=sw26),  # 10
    tool=dict(acap=nw,   pcap=nw,   pmat=nw))  # 6


class Cocomo(Thing):
  def __init__(i, listofdicts=[]):
    i.x, i.y, dd = o(), o(), kopy(Cocomo.defaults)
    # set up the defaults
    for d in dd:
      for k in dd[d]:
        i.x[k] = dd[d][k]  # can't +=: no background info
    # apply any other constraints
    for dict1 in listofdicts:
      for k in dict1:
        try:
          i.x[k] += dict1[k]  # now you can +=
        except Exception as e:
          print(k, e)
    # ----------------------------------------------------------
    for k in dd.misc:
      i.y[k] = i.x[k]()
    for k in dd.pos:
      i.y[k] = F(.073,  .21)() * (i.x[k]() - 3) + 1
    for k in dd.neg:
      i.y[k] = F(-.178, -.078)() * (i.x[k]() - 3) + 1
    for k in dd.sf:
      i.y[k] = F(-1.56, -1.014)() * (i.x[k]() - 6)
    # ----------------------------------------------------------

  def effort(i):
    em, sf = 1, 0
    b = (0.85-1.1)/(9.18-2.2) * i.x.a() + 1.1+(1.1-0.8)*.5
    for k in Cocomo.defaults.sf:
      sf += i.y[k]
    for k in Cocomo.defaults.pos:
      em *= i.y[k]
    for k in Cocomo.defaults.neg:
      em *= i.y[k]
    return round(i.x.a() * em * (i.x.goal()*i.x.kloc()) ** (b + 0.01*sf), 1)

  def risk(i, r=0):
    for k1, rules1 in rules.items():
      for k2, m in rules1.items():
        x = i.x[k1]()
        y = i.x[k2]()
        z = m[x-1][y-1]
        r += z
    return round(100 * r / 104, 1)
