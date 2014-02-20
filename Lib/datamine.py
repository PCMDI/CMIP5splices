import glob
import numpy as np
from collections import Counter
import cdms2 as cdms
import cdutil
import MV2 as MV
import cdtime
import difflib


def version_num(fname):
    v = fname.split("ver-")[1].split(".")[0]
    if v[0]=='v':
        return int(v[1:])
    else:
        return int(v)

def get_corresponding_var(fname,var='pr'):
    """Returns file name of a variable corresponding as close a spossible to the input filename
    Original Author: Kate Marvel
    Tweaked for multiple variables by: Charles Doutriaux
    """
    vari =fname.split(".")[7]
    if len(glob.glob(fname.replace(vari,var))) == 1:
        return glob.glob(fname.replace(vari,var))[0]
    else:
        fnames = glob.glob(fname.replace(vari,var).split(".ver")[0]+"*")
        if len(fnames)>0:
            i = np.argmax(map(version_num,fnames))
            return fnames[i]
        else:
            possmats = glob.glob(fname.replace(vari,var).split("cmip5.")[0]+"*")
            return difflib.get_close_matches(fname,possmats)[0]

def get_corresponding_control(fname):
    """Returns filename of picontrol corresponding to input filename
    Original Author: Kate Marvel
    """
    rn = fname.split(".")[2]
    rip = fname.split(".")[3]
    before_rip,after_rip = fname.replace(rn,"piControl").split(rip)
    before_ver = after_rip.split("ver")[0]
    fnames = glob.glob(before_rip+"r1i1p1"+before_ver+"*")
    
    if len(fnames)>0:
        i = np.argmax(map(version_num,fnames))
        return fnames[i]
    else:
        print "CORRESPONDING CONTROL NOT FOUND FOR "+fname
        
        possmats = glob.glob(fname.replace(rn,"piControl").split("cmip5.")[0]+"*")
        print "USING " +difflib.get_close_matches(fname,possmats)[0]
        return difflib.get_close_matches(fname,possmats)[0]


def get_latest_version(listoffiles):
    version_numbers = map(lambda x: x.split("ver-")[-1].split(".")[0], listoffiles)
    enums = []
    for num in version_numbers:
        
        if num[0] != "v":
            enums+=[int(num)]
        else:
            enums+=[int(num[1:])]
    
    i = np.argmax(enums)
    return listoffiles[i]

def get_ensemble(basedir,model,search_string = "*"):
    if model.find("GISS")>=0:
        if search_string == "*":
            search_string = "*p1.*"
        else:
            
            
            model = model.split(" ")[0]
        
        alldata = glob.glob(basedir+"*"+model+"."+search_string)
        
    else:
        alldata = glob.glob(basedir+"*."+model+"."+search_string)
    modified = []
    truncated = np.array(map(lambda x: x.split("ver")[0], alldata))
    c = Counter(truncated)
    for k in c.keys():
        I = np.where(truncated==k)[0]
        listoffiles = np.array(alldata)[I]
        if c[k]>1:
            modified += [get_latest_version(listoffiles)]
        else:
            modified += [listoffiles[0]]
    return modified


def get_coarsest_grid(basedir):
    gs = 1.e20
    grid = None
    the_file = None
    for fil in glob.glob(basedir+"*"):
        f = cdms.open(fil)
        variable = fil.split(".")[-4]
        g = f[variable].getGrid()
        if g.shape[0]*g.shape[1] < gs:
            gs = g.shape[0]*g.shape[1]
            
            the_file = fil
        f.close()
    f = cdms.open(the_file)
    grid = f(variable,time=slice(0,1)).getGrid()
    f.close()
    return the_file,grid


def ensemble_average(basedir, grid = None, func = None):
    models = np.unique(map(lambda x: x.split(".")[1],glob.glob(basedir+"*")))
    #Deal with extremely annoying GISS physics
    giss = np.where([x.find("GISS")>=0 for x in models])[0]
    oldmodels = models
    models = np.delete(models, giss)
    for gissmo in oldmodels[giss]:
        physics_versions = np.unique([x.split(".")[3][-2:] for x in glob.glob(basedir+"*"+gissmo+"*")])
        for pv in physics_versions:
            models = np.append(models, gissmo+" "+pv)
        
    
    if grid is None: #Get the coarsest grid
        the_file,grid = get_coarsest_grid(basedir)
    
    if "CESM1-WACCM" in models:
        i = np.argwhere(models == "CESM1-WACCM")
        models = np.delete(models,i)
    if "CanCM4" in models:
        i = np.argwhere(models == "CanCM4")
        models = np.delete(models,i)
        

    mo = models[0]
    print mo
    ens = get_ensemble(basedir,mo)
    ens0 = ens[0]
    print ens0
    f = cdms.open(ens0)
    variable = ens0.split(".")[-4]
    data = f(variable).regrid(grid,regridTool='regrid2')
    cdutil.setTimeBoundsMonthly(data)
    if func is not None:
        data = func(data)
    f.close()
    
    time_and_space = data.shape
    realizations = MV.zeros((len(ens),)+time_and_space)
    realizations[0] = data
    if len(ens)>1:
        for i in range(len(ens))[1:]:
            f = cdms.open(ens[i])
            print ens[i]
            data = f(variable).regrid(grid,regridTool='regrid2')
            f.close()
            cdutil.setTimeBoundsMonthly(data)
            if func is not None:
                data = func(data)
            realizations[i] = data
    
    model_average = MV.zeros((len(models),)+time_and_space)+1.e20
    j= 0
    model_average[j] = MV.average(realizations,axis=0)
    
    for mo in models[1:]:
        print mo
        j+=1
        ens = get_ensemble(basedir,mo)
        realizations = MV.zeros((len(ens),)+time_and_space)
        for i in range(len(ens)):
            f = cdms.open(ens[i])
            #print ens[i]
            data = f(variable).regrid(grid,regridTool='regrid2')
            f.close()
            cdutil.setTimeBoundsMonthly(data)
            if func is not None:
                data = func(data)
            print data.shape
            print time_and_space
            print data.shape == time_and_space
            if data.shape == time_and_space:
                realizations[i] = data
                masked_ma = False
            else:
                masked_ma = True
        
        if not masked_ma:
            model_average[j] = MV.average(realizations,axis=0)
        else:
            print "not the right shape: "+mo
            model_average[j] = MV.ones(time_and_space)+1.e20

    M2 = MV.masked_where(model_average>1.e10,model_average)
    M = MV.average(M2,axis=0)
    M.setAxisList(data.getAxisList())
    M.id = data.id
    M.name = M.id
    
    return M
    
            
    
if __name__ == "__main__":
    rn = "historical-rcp85"
    start = cdtime.comptime(1865,1,1)
    stop = cdtime.comptime(2050,12,31)
    func = lambda x: x(time=(start,stop))
    tbasedir = "/work/cmip5/"+rn+"/atm/mo/tas/"
    pbasedir = "/work/cmip5/"+rn+"/atm/mo/pr/"
    
    tas = ensemble_average(tbasedir,func = func)
    f = cdms.open("/export/marvel1/PT/DATA/cmip5.MMA."+rn+".r1i1p1.mo.atm.Amon.tas.ver-1.latestX.nc","w")
    f.write(tas)
    f.close()

    pr = ensemble_average(pbasedir,func = func)
    f = cdms.open("/export/marvel1/PT/DATA/cmip5.MMA."+rn+".r1i1p1.mo.atm.Amon.pr.ver-1.latestX.nc","w")
    f.write(pr)
    f.close()
    

