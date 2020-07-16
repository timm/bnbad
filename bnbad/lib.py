import random,traceback,pprint, sys, re, argparse

def arg(txt,**d):
  """
  Support code for Command-line Options. Argument
  types are inferred by peeking at the default.
  Different types then lead to different kinds of options.
  Returns

     keyword,default,dictionary

  where dictionary contains the arguments needed by the
  command-line process `argparse`.
  """
  for k in d:
    key = k
    val = d[k]
    break
  default = val[0] if isinstance(val,list)  else val
  if val is False :
    return key,default,dict(help=txt, action="store_true")
  else:
    m,t = "S",str
    if isinstance(default,int)  : m,t= "I",int
    if isinstance(default,float): m,t= "F",float
    if isinstance(val,list):
      return key,default,dict(help=txt, choices=val,          
                      default=default, metavar=m ,type=t)
    else:
      eg = "; e.g. -%s %s"%(key,val) if val != "" else ""
      return key,default, dict(help=txt + eg,
                      default=default, metavar=m, type=t)
  
def args(f,hello=""):
  """
  Link to Python's command line option processor.
  """
  lst = f()
  before = re.sub(r"\n  ","\n", hello)
  parser = argparse.ArgumentParser(description = before,
             formatter_class = argparse.RawDescriptionHelpFormatter)
  for key, _,args in lst:
    parser.add_argument("-"+key,**args)
  return parser.parse_args()

class Thing:
  """
  All my classes are Things that pretty print themselves
  by reporting themselves as nested dictionaries then 
  pprint-ing that dictionary.
  """
  def __repr__(i):
     return re.sub(r"'",' ', 
                   pprint.pformat(dicts(i.__dict__),compact=True))

def dicts(i,seen=None):
  """
  This is a tool used by `Thing`.
  Converts `i` into a nested dictionary, then pretty-prints that.
  """
  if isinstance(i,(tuple,list)): 
    return [ dicts(v,seen) for v in i ]
  elif isinstance(i,dict): 
    return { k:dicts(i[k], seen) for k in i if str(k)[0] !="_"}
  elif isinstance(i,Thing): 
    seen = seen or {}
    j =id(i) % 128021 # ids are LONG; show them shorter.
    if i in seen: return f"#:{j}"
    seen[i]=i
    d=dicts(i.__dict__,seen)
    d["#"] = j
    return d
  else:
    return i

class o(Thing):
  def __init__(i,**d) : i.__dict__.update(**d)

def rows(x=None):
  "Read a csv file from disk."
  prep=lambda z: re.sub(r'([\n\t\r ]|#.*)','',z.strip())
  if x:
    with open(x) as f:
      for y in f: 
         z = prep(y)
         if z: yield z.split(",")
  else:
   for y in sys.stdin: 
         z = prep(y)
         if z: yield z.split(",")

def cols(src):
  "Ignore columns if, on line one, the name contains '?'."
  todo = None
  for a in src:
    todo = todo or [n for n,s in enumerate(a) if not "?"in s]
    yield [ a[n] for n in todo]

def pairs(lst):
  "Return the i-th and i+1-th item in a list."
  last=lst[0]
  for i in lst[1:]:
    yield last,i
    last = i

def shuffle(lst):
  "Return a shuffled list."
  random.shuffle(lst)
  return lst

def has(i,seen=None):
  """
  Report a nested object as a set of nested lists.
  If we see the same `Thing` twice, then show it the 
  first time, after which, just show its id. Do not 
  return anything that is private;
  i.e. anything whose name starts with "_".
  """
  seen = seen or {}
  if isinstance(i,Thing): 
     j =id(i) % 128021
     if i in seen: return f"#:{j}"
     seen[i]=i
     d=has(i.__dict__,seen)
     d["#"] = j
     return d
  if isinstance(i,(tuple,list)): 
     return [ has(v,seen) for v in i ]
  if isinstance(i,dict): 
     return { k:has(i[k], seen) for k in i if str(k)[0] !="_"}
  return i

def dprint(d, pre="",skip="_"):
  """
  Pretty print a dictionary, sorted by keys, ignoring 
  private slots (those that start with '_'_).
  """
  def q(z):
    if isinstance(z,float): return "%5.3f" % z
    if callable(z): return "f(%s)" % z.__name__
    return str(z)
  l = sorted([(k,d[k]) for k in d if k[0] != skip])
  return pre+'{'+", ".join([('%s=%s' % (k,q(v))) 
                             for k,v in l]) +'}'

def perc(a,p=[.25,.5,.75]):
  ls = sprted(a)
  return [ l[int(p0 * len(a))] for p0 in p ]

def xtile(lst,lo=0,hi=1,
             width = 50,
             chops = [0.1 ,0.3,0.5,0.7,0.9],
             marks = [" " ,".","."," "," "],
             bar   = "",
             star  = "o",
             show  = " %5.3f"):
    """
    Pretty print a large list of numbers.
    Take a list of numbers, sort them,
    then print them as a
    horizontal
    xtile chart (in ascii format). The default is a
    contracted _quintile_ that shows the
    10,30,50,70,90 breaks in the data (but this can be
    changed- see the optional flags of the function).
    """
    def at(p): 
      return ordered[int(len(lst)*p)]
    def norm(x): 
      return int(width*float((x - lo))/(hi - lo+0.00001))
    def pretty(lst):
      return ', '.join([show % x for x in lst])
    ordered = sorted(lst)
    what    = [at(p)   for p in chops]
    where   = [norm(n) for n in  what]
    out     = [" "] * width
    marks1 = marks[:]
    for one,two in pairs(where):
      for i in range(one,two):
        out[i] = marks1[0]
      marks1 = marks1[1:]
    if bar:  out[int(width/2)]  = bar
    if star: out[norm(at(0.5))] = star
    return ''.join(out) +  "," +  pretty(what)

