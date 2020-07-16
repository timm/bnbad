from .lib import *
from .my import *

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
  def score(s): 
    t,f = Test.t, Test.f
    return f"#TEST {s} passes = {t-f} fails = {f}"
  def go(fn=None, use=None):
    all =Test.all
    if fn:
      all[fn.__name__] = fn
    elif use:
      [Test.run(all[k]) for k in all if use in k]
    else: 
      [Test.run(all[k]) for f in all]
  def run(fun):    
    try:
      Test.t += 1
      print("### ",fun.__name__)
      doc = fun.__doc__ or ""
      print( "# "+ re.sub(r"\n[ ]*","\n# ",doc) )
      print("")
      random.seed(my.r)
      fun()
      print(Test.score("PASS"),':',fun.__name__)
    except Exception:
      Test.f += 1
      print(traceback.format_exc())
      print(Test.score("FAIL"),':',fun.__name__)
  def list():
    print("")
    print(__file__ + " -t [NAME]") 
    print("\nKnown test names:")
    for name,fun in Test.all.items():
      if name != "test_tests":
        name = re.sub(r"test_","",name)
        doc = fun.__doc__ or ""
        doc = re.sub(r"\n[ ]*","",doc)
        print(f"  {name:10s} : {doc}")
 
