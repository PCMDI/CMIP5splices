import cdms2
import cdutil
import os
import glob
import argparse
import genutil
import sys
import cmip5utils
import numpy
import MV2
value = 0 
cdms2.setNetcdfShuffleFlag(value) ## where value is either 0 or 1
cdms2.setNetcdfDeflateFlag(value) ## where value is either 0 or 1
cdms2.setNetcdfDeflateLevelFlag(value) ## where value is a integer between 0 and 9 included

p = argparse.ArgumentParser(description="Produces (model,time,level) global averages")

p.add_argument('-e','--exp',default='abrupt4xCO2')
p.add_argument('-v','--var',default='ta')
p.add_argument('-T','--table',default='Amon')
p.add_argument('-r','--rip',default='r1i1p*')
p.add_argument('-R','--realm',default='atm')
p.add_argument('-o','--output',default='.')
p.add_argument('-i','--input',default='/work/cmip5/')
p.add_argument('-t','--time',default='min',choices=["max","min","common"])
p.add_argument('-m','--minimum_time_length',default=360,type=int)
p.add_argument('-d','--debug',default=True)
p.add_argument('-l','--levels',type=int,nargs="+",default=[1000,925,850,700,600,500,400,300,250,200,150,100,70,50,30,20,10])
p.add_argument('-a','--add_pr',default=True)


p = p.parse_args(sys.argv[1:])
print p

tmpl = genutil.StringConstructor(os.path.join(p.input,"%(exp)","%(realm)","mo","%(var)","*%(model)*%(rip)*%(table)*.xml"))

tmpl.exp = p.exp
tmpl.var = p.var
tmpl.realm = p.realm
tmpl.rip=p.rip
tmpl.table=p.table
tmpl.model="*"

print tmpl()

lst = glob.glob(tmpl())
print lst

models = {}
for l in lst:
  sp = l.split(".")
  m=sp[1]
  r=sp[3]
  if models.has_key(m):
    if not r in models[m]:
      models[m].append(r)
  else:
    models[m]=[r,]

print models

nmod = len(models.keys())
files = []
starts = []
ends=[]
models_axis = []

for m in models.keys():
  tmpl.model=m
  for r in models[m]:
    tmpl.rip=r
    fnm = glob.glob(tmpl())
    if len(fnm)==0:
      print "WHATTTT!",m,tmpl()
    elif len(fnm)>1:
      fnm = cmip5utils.datamine.get_latest_version(fnm)
    else:
      fnm=fnm[0]
    f=cdms2.open(fnm)
    V=f[p.var]
    t=V.getTime()
    if p.time=="max":
      starts=[0,]
      ends.append(len(t))
    elif p.time=="min":
      starts=[0,]
      print m,len(t),p.minimum_time_length,type(p.minimum_time_length)
      if len(t)>p.minimum_time_length:
        ends.append(len(t))
      else:
        continue
    else:
      tc=t.asComponentTime()
      starts.append(tc[0])
      ends.append(tc[-1])
    models_axis.append("%s.%s" % (m,r))
    files.append(fnm)

if p.time=="max":
  start = min(starts)
  end = max(ends)
  Nt = end/12
elif p.time=="min":
  start = max(starts)
  end = min(ends)
  iend = numpy.argmin(ends)
  print iend,models_axis[iend]
  Nt = end/12
elif p.time=="common":
  start=max(starts)
  end=min(ends)

print len(models),"from",start,"to",end

N=len(files)
##Ok now we are going to loop thru levels and we then run cdscan on it
if p.add_pr:
  p.levels.append(0)
failed_models = []
for l in p.levels:
  models_used = []
  V=p.var
  if l==0:
    V="pr"
  fnmo = os.path.join(p.output,p.exp,p.realm,"mo",V,"%s_%s_%i.nc" % (V,p.exp,l))
  if os.path.exists(fnmo):
    print l,"already here, skipping"
    continue
  out=None
  for i,fnm in enumerate(files[:N]):
    if fnm in failed_models:
      continue
    tmp = numpy.ma.ones((1,Nt,1))*1.e20
    if l==0:
      fnm= cmip5utils.datamine.get_corresponding_var(fnm,"pr")
    f=cdms2.open(fnm)
    print f.variables,f[V]
    print models_axis[i],f[V].shape,'in file',f[V].getLevel()
    if f[V].shape[0]<Nt/2:
      #Not enough times skip it
      print "Skipping:",models_axis[i]
      continue
    if p.time=="min":
      Nkeep = end
    elif p.time=="max":
      Nkeep=None
    if p.time=="common":
      Time = (start,end)
    else:
      tc=f[V].getTime().asComponentTime()
      istart=0
      while tc[istart].month!=1:
        istart+=1
      Time = slice(istart,istart+Nkeep)
    kargs = {"time":Time}
    if l!=0:
      kargs["level"]=(l*100.,l*100.)
    try:
      s=f(V,**kargs)
    except:
      "Model error:",m,l
      failed_models.append(fnm)
      continue
    models_used.append(models_axis[i])
    print s.shape,'read'
    s=cdutil.averager(s,axis='xy')
    print s.shape,'averaged'
    cdutil.times.setTimeBoundsMonthly(s)
    s=cdutil.times.YEAR(s,criteriaarg=[.9999,None])
    print s.shape,"yearlied"
    if p.time=="max":
      raise Exception,"crp"
    else:
      if l==0:
        tmp[:,:,:] = s.asma()[numpy.newaxis,:,numpy.newaxis]
      else:
        tmp[:]=s[:]
    if out is None:
      out=tmp
    else:
      out=numpy.ma.concatenate((out,tmp),axis=0)
  out=MV2.array(out)
  M=cdms2.createAxis(numpy.arange(len(models_used)))
  M.id = "models"
  M.models = repr(models_used)
  print out.shape
  print len(M)
  out.setAxis(0,M)
  if p.time=="common":
    t=s.getTime()
  else:
    t=cdms2.createAxis(range(Nt))
    t.designateTime()
    t.id="time"
    t.units="years since 1900"
    cdutil.times.setTimeBoundsYearly(t)
  t.toRelativeTime("months since 1800")
  out.setAxis(1,t)
  if l!=0:
    L=cdms2.createAxis([l*100.,])
    L.id=s.getLevel().id
    L.designateLevel()
    L.units="Pa"
    out.setAxis(2,L)
  else:
    out=out[...,0]
  try:
    os.makedirs(os.path.dirname(fnmo))
  except Exception,err:
    print err
    pass
  f=cdms2.open(fnmo,"w")
  f.history = repr(sys.argv)
  f.write(out,id=V)
  f.close()

os.chdir(os.path.dirname(fnmo))
levs = numpy.array(p.levels)*100.
levs = str(levs.tolist()).replace(" ","")[1:-1]
cmd = "cd %s; cdscan -x %s_%s.xml -l %s %s_%s*.nc" % (os.getcwd(),p.var,p.exp,levs,p.var,p.exp,)
if p.add_pr:
  cmd+=" ../pr/pr_%s*.nc" % (p.exp)
print "Failed models:",failed_models
print "CMD",cmd
print os.getcwd()
import subprocess,shlex
P=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
o,e = P.communicate()
print o
print e

