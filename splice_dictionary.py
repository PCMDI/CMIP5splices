import genutil
import os
import numpy as np
import fnmatch
from datetime import datetime
import cdms2 as cdms
from string import upper,lower

def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        files = [os.path.join(path,f) for f in files]
        for filename in fnmatch.filter(files, pattern):
            yield filename

def parse_filename(fname):
    '''Parse the full path+filename.  Return a dictionary whose keys are model metadata.'''
    try:
        root,work,cmip,experiment,realm,mo_new,variable,filename = fname.split("/")
        cmip,model,experiment,rip,mo,realm,tableid,variable,version,ext = filename.split(".")
    except:
        print "filename must be of the form %(root)%(experiment)/%(realm)/mo/%(variable)/cmip5.%(model).%(experiment).%(rip).mo.%(realm).%(variable).%(version).xml"
        raise TypeError
    d = {}
    d["root"]="/".join([root,work,cmip,""])
    d["experiment"] = experiment
    d["realm"] = realm
    d["variable"] = variable
    d["model"] = model
    d["rip"] = rip
    d["version"] = version
    d["time_frequency"] = mo_new
    d["tableid"] = tableid
    return d

def newest_version(listoffiles):
    versions = np.array([x.split("ver-")[1].split(".")[0] for x in listoffiles])
    d = parse_filename(listoffiles[0])
    model = d["model"]
    version_numbers = [float(x.split("v")[-1]) for x in versions]
    if upper(model) == "CSIRO":
        less_than_1000 = np.where(np.array(version_numbers <1000.))
        I = np.argmax(version_numbers[less_than_1000])
    else:
         I = np.argmax(version_numbers)
         
    return listoffiles[I]
    
    

def check_parentage(fname):

    d = parse_filename(fname)
    openf = cdms.open(fname)
    meta_r = str(openf.attributes["realization"])
    
    meta_i = str(openf.attributes["initialization_method"])
    meta_p = str(openf.attributes["physics_version"])
    meta_rip = "r"+meta_r+"i"+meta_i+"p"+meta_p
    parent_rip = openf.attributes["parent_experiment_rip"]
    if meta_rip != d["rip"]:
        print "model rip and metadata rip do not match"
        return 0
    if meta_rip != parent_rip:
        print "model rip and parent rip do not match"
        return 1
    parent = openf.attributes["parent_experiment"]
    if parent != "historical":
        print "parent experiment is "+parent
        return 2
    d["experiment"] = parent
    d["version"] = "*"
    return newest_version([x for x in find_files(d)])
    
    
    
        
        

def find_files(d,print_search_string = False):
    '''Return all datafiles that match criteria specified in the dictionary d'''
    template = "%(root)%(experiment)/%(realm)/%(time_frequency)/%(variable)/cmip5.%(model).%(experiment).%(rip).mo.%(realm).%(tableid).%(variable).%(version).xml"
    
    filename = genutil.StringConstructor(template)
    
    # set defaults
    [setattr(filename,k,"*") for k in filename.keys()]
    # by default root is /work/cmip5/
    filename.root = "/work/cmip5/"

    #set filename attributes
    
    [setattr(filename,k,d[k]) for k in d.keys()]
    if print_search_string:
        print filename()
   #Get most complete specified directory
    

    return locate(filename(),root = filename.root)
    
time = str(datetime.now())
user = os.environ["USER"]
#d = {}
#d[user+" "+time] = {}



