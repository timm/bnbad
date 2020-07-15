<p align=center> 
<img src="https://img.shields.io/badge/license-mit-red"> <img 
src="https://img.shields.io/badge/language-python-orange"> <img 
src="https://img.shields.io/badge/purpose-ai,se-blueviolet"> <img 
src="https://img.shields.io/badge/platform-mac,*nux-informational"><a 
     href="https://travis-ci.org/github/sehero/lua"> <img 
src="https://travis-ci.org/aiez/eg.svg?branch=master"></a><a 
     href="https://zenodo.org/badge/latestdoi/263210595"> <img 
src="https://zenodo.org/badge/263210595.svg" alt="DOI"></a><a 
     href='https://coveralls.io/github/aiez/lua?branch=master'> <img i
src='https://coveralls.io/repos/github/aiez/eg/badge.svg?branch=master' alt='Coverage Status' /></a></p>

<h1 align=center><a href="/README.md#top">Break 'n Bad</a></h1>
<h3 align=center> Fast, explicable, multi-objective optimization</h3> 
<p align=center>
<a
href="http://menzies.us/bnbad">docs</a> :: <a
href="#install">install</a> :: <a
href="https://github.com/timm/bnbad/issues">issues</a> :: <a
href="LICENSE.md">license</a> :: <a
href="CONTRIBUTING.md">contribute</a> :: <a
href="CITATION.md">cite</a> ::  <a
href="CONTACT.md">contact</a>  
</p>

<img  align=right width=400 
src="docs/letscook.png">


BnBAD is a multi-objective optimizer
that reasons by breaking up problems into regions of `bad` and
`better`, then looks for ways on how to jump between those regions.

BnBAD might be a useful choice when:

- users have to trade-off competing goals, 
- succinct explanations are needed about what the system is doing,
- those explanations have to include ranges within which it is safe
  to change the system, 
- guidance is needed for how to improve things
  (or know what might make things worse); 
- thing being studied is constantly changing so:
   - we have to perpetually check if the current system is still trustworthy
   - and, if not, we need to update our models

## Install

Run as super user

    python3 setup.py install

## Technical Notes: 

- `bad` and `better` are score via 
  [Zitler's continuous domination predicate](docs/index.html#bnbad.Tab.better)
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


