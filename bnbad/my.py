"""
Config options.
"""

from .lib import arg, o


def help():
  """
  Define options.
  """
  h = arg
  return [
      h("bin min size =len**b",                            b=.5),
      h("what columns to while tree building",      c=["x", "y"]),
      h("use at most 'd' rows for distance calcs",         d=256),
      h("merge ranges whose scores differ by less that F", e=0.05),
      h("separation of poles (f=1 means 'max distance')",  f=.9),
      h("decision list: minimum leaf size",                M=10),
      h("decision list: maximum height",                   H=4),
      h("decision list: ratio of negative examples",       N=4),
      h("coefficient for distance",                        p=2),
      h("random number seed",                              r=1),
      h("tree leaves must be at least n**s in size",       s=0.5),
      h("stats: Cliff's Delta 'dull'",    Sdull=[.147, .33, .474]),
      h("stats: Coehn 'd'",                           Scohen=0.2),
      h("stats: number of boostrap samples",               Sb=500),
      h("stats: bootstrap confidences",                    Sconf=0.01),
      h("training data (arff format",           train="train.csv"),
      h("testing data (csv format)",               test="test.csv"),
      h("List all tests",                                  L=False),
      h("Run all tests",                                   T=False),
      h("Verbose mode",                                    V=False),
      h("Run just the tests with names matching 'S'",      t="")
  ]


my = o(**{k: d for k, d, _ in help()})
