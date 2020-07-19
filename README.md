<h1 align=center> BnBAD (break 'n bad)</h3> 
<img  align=center width=300 src="docs/letscook.png">
<h3 align=center> Fast, explicable, multi-objective reasoning</h3> 

<p align=center>
<a
href="http://menzies.us/bnbad">read the docs</a> :: <a
href="#install">install</a> :: <a
href="https://github.com/timm/bnbad/issues">issues</a> :: <a
href="LICENSE.md">license</a> :: <a
href="CONTRIBUTING.md">contribute</a> :: <a
href="CITATION.md">cite</a> ::  <a
href="CONTACT.md">contact</a>  
</p>

<p align=center>
<a href="LICENSE.md"><img 
src="https://img.shields.io/badge/license-mit-red"></a> <img 
src="https://img.shields.io/badge/purpose-ai,se-blueviolet"> <a 
     href="https://travis-ci.org/github/timm/bnbad"> <img 
src="https://travis-ci.org/timm/bnbad.svg?branch=master"></a> <a
href="https://doi.org/10.5281/zenodo.3947026"><img 
src="https://zenodo.org/badge/DOI/10.5281/zenodo.3947026.svg" alt="DOI"></a>
</p>

<hr>



BnBAD is a multi-objective optimizer
that reasons by:

1. breaking up problems into regions of `bad` and
`better`;
2.  then looks for ways on how to jump between those regions.

```
:-------:  
| Ba    | Bad <----.  planning= (better - bad)
|    56 |          |  monitor = (bad - better)
:-------:------:   |  
        | B    |   v  
        |    5 | Better  
        :------:
```

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

Download the repo or the zip from http://github.com/timm/bnbad

In the same directory as the `setup.py` file....

Install pypy3:

    brew install pypy3      # mac os/x
    sudo apt install pypy3  # unix

Install support packages into the pypy3 space:

    pip3      install colorterm rerun
    pip_pypy3 install colorterm rerun # optional.. if you want speed

Install `bnbad` using `setup.py`:

    python3 setup.py install
    pypy3   setup.py install # optional.. if you want speed

## Technical Notes: 

- Examples are clustered in goal
  space and the `better` cluster is the one that dominates all the
  other `bad` clusters.
- `bad` and `better` are score via [Zitler's continuous domination predicate](docs/index.html#bnbad.Tab.better)
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

## Usage

### Command-Line Usage

Step1: prepare a data file whose first line shows what
are the numbers, what are the symbols, and what
goals are to be
minimized or maximized. For example, here we want to
maximize _acceleration_ and miles per hour (_mpg_) and minimize _weight_.
As to the other columns:

-  _$displacement_ and _$horsepower_ and _$model_ are numeric
- and _cylinders_ and _origin_ are symbolic

```csv
cylinders, $displacement, $horsepower, <weight, >acceleration, $model,  origin, >!mpg
8,         304,           193,         4732,    18.5,          70,      1,      10
8,         360,           215,         4615,    14,            70,      1,      10
8,         307,           200,         4376,    15,            70,      1,      10
8,         318,           210,         4382,    13.5,          70,      1,      10
.....
```

```
usage: __init__.py [-h] [-treeVerbose] [-b F] [-c S] [-d I] [-e F] [-f F]
                   [-M I] [-H I] [-N I] [-p I] [-r I] [-s F] [-train S]
                   [-test S] [-L] [-T] [-t S]


optional arguments:
  -h, --help    show this help message and exit
  -treeVerbose  verbose mode for Tree
  -b F          bin min size =len**b; e.g. -b 0.5
  -c S          what columns to while tree building
  -d I          use at most 'd' rows for distance calcs; e.g. -d 256
  -e F          merge ranges whose scores differ by less that F; e.g. -e 0.05
  -f F          separation of poles (f=1 means 'max distance'); e.g. -f 0.9
  -M I          decision list leaf, minimum size; e.g. -M 10
  -H I          decision list maximum height; e.g. -H 4
  -N I          decision lists, ratio of negative examples; e.g. -N 4
  -p I          coefficient for distance; e.g. -p 2
  -r I          random number seed; e.g. -r 1
  -s F          tree leaves must be at least n**s in size; e.g. -s 0.5
  -train S      training data (arff format; e.g. -train train.csv
  -test S       testing data (csv format); e.g. -test test.csv
  -L            List all tests.
  -T            Run all tests.
  -t S          Run just the tests with names matching 'S'
```
