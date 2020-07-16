from .lib import *

def help(): 
  """
  Define options.
  """
  return [
    arg("verbose mode for Tree",                          treeVerbose= False),
    arg("bin min size =len**b",                           b= .5),
    arg("what columns to while tree building " ,          c= ["x","y"]),
    arg("use at most 'd' rows for distance calcs",        d= 256),
    arg("merge ranges whose scores differ by less that F",e= 0.05),
    arg("separation of poles (f=1 means 'max distance')", f= .9),
    arg("decision list: minimum leaf size",               M= 10),
    arg("decision list: maximum height",                   H= 4),
    arg("decision list: ratio of negative examples",     N= 4),
    arg("coefficient for distance" ,                      p= 2),
    arg("random number seed" ,                            r = 1),
    arg("tree leaves must be at least n**s in size" ,     s= 0.5),
    arg("stats: Cliff's Delta 'dull'",                    Sdull=[.147,.33,.474]),
    arg("stats: Coehn 'd'",                               Scohen=0.2),
    arg("stats: number of boostrap samples",              Sb=500),
    arg("stats: bootstrap confidences",                   Sconf=0.01),
    arg("training data (arff format",                     train= "train.csv"),
    arg("testing data (csv format)",                      test=  "test.csv"),
    arg("List all tests.",                                L = False),
    arg("Run all tests.",                                 T = False),
    arg("Run just the tests with names matching 'S'",     t= "")
  ]

my  = o(**{k:d for k,d,_ in help()})
