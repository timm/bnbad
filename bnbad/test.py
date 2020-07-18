from .lib import *
from .my import *
from termcolor import colored

def go(fn=None,use=None):  
  """
  Decorator for test functions. 
  Adds the function to `Test.all`.
  """
  Test.go(fn=fn,use=use); return fn

class Test:
  """
  Unit test manager. Stores all the tests in `Test.all`. 
  Lets you list the tests, run some of them, or all.
  """
  t,f = 0,0
  all = {}
  def score(s,color): 
    t,f = Test.t, Test.f
    return colored(f"{s} pass {t-f: >3} fail {f: >3} ",color)
  def go(fn=None, use=None):
    all =Test.all
    if fn:
      all[fn.__name__] = fn
    elif use:
      [Test.run(all[k]) for k in all if use in k]
    else: 
      [Test.run(all[k]) for k in all if k != "test_tests"]
  def run(fun):    
    try:
      Test.t += 1
      doc = fun.__doc__ or ""
      random.seed(my.r)
      fun()
      print(Test.score("💚","green")+fun.__name__)
    except Exception:
      Test.f += 1
      print(traceback.format_exc(limit=2))
      print(Test.score("💔" ,"red")+fun.__name__)
  def list():
    print("")
    print(__file__ + " -t [NAME]") 
    print("\nKnown test names:")
    for name,fun in Test.all.items():
      if name != "test_tests":
        name = re.sub(r"test_","",name)
        doc = fun.__doc__ or ""
        doc = doc.split("\n")[0]
        doc = re.sub(r"\n[ ]+","",doc)
        doc = re.sub(r"^[ ]+","",doc)
        print(f"  {name:10s} : {doc}")
 
