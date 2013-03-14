import genutil
import os
import numpy as np
import fnmatch
from datetime import datetime
import cdms2 as cdms
from string import upper,lower
import collections

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
    """Get the newest version of the xml according to Jeff Painter's instructions."""
    if type(listoffiles) is not type([]):
        return listoffiles
    if len(listoffiles)==1:
        return listoffiles[0]
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
    """Returns either the parent file or list of strings with errors"""
    d = parse_filename(fname)
    openf = cdms.open(fname)
    keys = openf.attributes.keys()
    flags = []
    if "realization" not in keys:
        flags+[ "no realization specified"]
        meta_r="NA"
    else:
        meta_r = str(openf.attributes["realization"])


    if "initialization_method" not in keys:
        flags+=[ "no initialization specified"]
        meta_i="NA"
    else:
        meta_i = str(openf.attributes["initialization_method"])
    if "physics_version" not in keys:
        flags+=["no physics version specified"]
        meta_p = "NA"
    else:
        meta_p = str(openf.attributes["physics_version"])

    meta_rip = "r"+meta_r+"i"+meta_i+"p"+meta_p

    if "parent_experiment_rip" not in keys:
        flags+=["parent_experiment_rip not specified"]
        parent_rip="NA"
    else:
        parent_rip = openf.attributes["parent_experiment_rip"]

    if meta_rip != d["rip"]:
        flags+=["model rip ("+d["rip"]+") and metadata rip ("+meta_rip+") do not match"]

    if meta_rip != parent_rip:
        flags+=["metadata rip ("+meta_rip+") and parent rip ("+parent_rip+") do not match"] 

    if "parent_experiment" not in openf.attributes.keys():
        flags+=["no parent experiment specified"]
        parent = "NA"
    else:    
        parent = openf.attributes["parent_experiment"]
        if lower(parent) != "historical":
            flags+=["parent experiment is "+parent]
      
    if "branch_time" not in openf.attributes.keys():
        flags +=["branch time not specified"]
    
    d["experiment"] = "historical"
    d["version"] = "*"
    files = list(find_files(d))
    if len(files)==0:
        flags+=["parent file not found in "+d["root"]]
    if len(flags)==0:
        return newest_version(files)
    else:
        return flags
        
            
        

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


def remove_duplicate_versions(listoffiles):
    remove_this = []
    remove_version = lambda x: x.split(".ver")[0]
    files_rv = map(remove_version, listoffiles)
    dcounter = collections.Counter(files_rv)
    duplicates = [n for n, i in dcounter.iteritems() if i > 1]
    for dupe in duplicates:
        
        versions = [listoffiles[x] for x in np.argwhere([x.find(dupe)==0 for x in files_rv])]
        
        nv = newest_version(versions)
        for version in versions:
            if version != nv:
                remove_this +=[version]
    [listoffiles.remove(x) for x in remove_this]
    return listoffiles
def flag(d,latest_version_only = True):
    """Use the check_parentage function to flag files with potential splicing issues.   """
    flagged = {}
    ok = {}
    all_files = find_files(d)
    if latest_version_only:
        all_files = remove_duplicate_versions(list(all_files))
    for f in all_files:
        parent = check_parentage(f)
        if type(parent)==type([]):
            flagged[f]=parent
        else:
            ok[f] = parent
    return flagged, ok


