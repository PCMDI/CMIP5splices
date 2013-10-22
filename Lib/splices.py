import cdms2
import os
import numpy
import cdtime
import sys

def commonprefix(*args):
    return os.path.commonprefix(args).rpartition('/')[0]

def dataType(obj):
    if isinstance(obj,(numpy.ndarray,cdms2.tvariable.TransientVariable)) and len(obj)==1:
        if obj.dtype == numpy.float32:
            return "Float"
        elif obj.dtype in [numpy.int,numpy.int64]:
            return "Long"
        elif obj.dtype == numpy.int32:
            return "Int"
        elif obj.dtype in [numpy.float,numpy.float64]:
            return "Double"
        
    if isinstance(obj,(int,numpy.int,numpy.int32,numpy.int64)):
        return "Long"
    elif isinstance(obj,(numpy.float32)):
        return "Float"
    elif isinstance(obj,(float,numpy.float,numpy.float64)):
        return "Double"
    elif isinstance(obj,str):
        return "String"
    elif obj is None:
        return "None"
    else:
        raise Exception,"Unknown type (%s) for attribute: %s" % (type(obj),obj)

def dataTypeAndValue(obj,a):
    v = getattr(obj,a)
    if isinstance(v,(numpy.ndarray,cdms2.tvariable.TransientVariable)) and len(v)==1:
        return dataType(v),v[0]
    else:
        return dataType(v),v

class Splicer(object):
    def __init__(self,spawn,origin=None,branch=None):
        return 
    def findOrigin(self,origin):
        return
    def findBranchTime(self):
        return

class CMIP5Splicer(Splicer):
    def __init__(self,spawn,origin=None,branch=None,type=None,output='screen',units='',debug=False):
        """Initialize the class with spwan file"""
        self.debug = debug
        print "DEBUG",self.debug
        self.output=output
        if spawn[0]!='/': # Sets it to full path
            pwd = os.getcwd()
            if self.debug:
                print pwd
            spawn = os.path.join(pwd,spawn)
        self.spawn=cdms2.open(spawn)
        self.units=units
        try:
            pass 
        except Exception,err:
            raise RuntimeError,"Could not load spawn file (%s) into cdms2: %s" % (spawn,err)
        if self.debug:
            print "Calling find origin"
        self.origin = self.findOrigin(origin)
        if self.debug:
            print "Origin:",self.origin
        self.branch = self.findBranchTime(branch,type)
        if self.debug:
            print "Branch:",self.branch

    def findOrigin(self,origin):
        """Automatically finds the origin from which spawn comes from"""
        if self.debug:
            print "are we even getting here?"
        if origin is not None:
            try:
                self.origin=cdms2.open(origin)
                return self.origin
            except:
                raise RuntimeError,"Could not load origin file (%s) into cdms2" % origin

        pnm = getattr(self.spawn,"uri",self.spawn.id).replace(self.spawn.experiment_id,self.spawn.parent_experiment_id)
        if self.debug:
            print "pnm:",pnm
        pnm = pnm.replace("r%ii%ip%i" % (self.spawn.realization,self.spawn.initialization_method,self.spawn.physics_version),self.spawn.parent_experiment_rip)
        self.origin = cdms2.open(pnm)
        return self.origin

    def genXml(self):
        if self.output=='screen':
            f=sys.stdout
        else:
            f=open(self.output,"w")
        print >> f, """<?xml version="1.0"?>
        <!DOCTYPE dataset SYSTEM "http://www-pcmdi.llnl.gov/software/cdms/cdml.dtd">
        <dataset
        """
        ## First figure out which vars are time dep
        tvars=[]
        nvars=[]
        for V in self.spawn.variables:
            for a in self.spawn[V].getAxisList():
                if a.isTime():
                    tvars.append(V)
                    break
            else:
                nvars.append(V)
        # Find common path
        cmndir = commonprefix(self.spawn.id,self.origin.id)+"/"
        if cmndir=='/':
            cmndir=""
            f1 = self.spawn.id
            f2 = self.origin.id
        else:
            f1 = self.spawn.id.split(cmndir)[1]
            f2 = self.origin.id.split(cmndir)[1]
        if self.debug:
            print cmndir,"*****",f1,"*****",f2,"xxxxx",nvars,"xxxx",tvars
        if len(nvars)!=0:
            cdmsfmp="[[%s,[[-,-,-,-,-,%s]]],[%s,[[0,%i,-,-,-,%s],[%i,%i,-,-,-,%s]]]]" % (str(nvars),f1,str(tvars),self.branch,f2,self.branch,self.branch+len(self.spawn[tvars[0]].getTime()),f1)
        else:
            cdmsfmp="[[%s,[[0,%i,-,-,-,%s],[%i,%i,-,-,-,%s]]]]" % (str(tvars),self.branch,f2,self.branch,self.branch+len(self.spawn[tvars[0]].getTime()),f1)
        ## ok get info from spawn
        specials = ['institution','calendar','frequency','Conventions','history']
        for a in specials:
            if not hasattr(self.spawn,a):
                continue
            print >> f,'%s = "%s"' % (a,getattr(self.spawn,a))

        print >> f, 'cdms_filemap = "%s"' % cdmsfmp.replace("'","")
        print >> f, 'directory = "%s"' % cmndir
        print >> f, 'id = "none"'
        print >> f,">"

        for a in self.spawn.attributes:
            if a in specials:
                continue
            A,v = dataTypeAndValue(self.spawn,a)
            print >>f, '<attr datatype="%s" name="%s" >%s</attr>' % (A,a,v)
        print >> f, '<attr datatype="String" name="cdsplice_origin">%s</attr>' % self.origin.id
        print >> f, '<attr datatype="String" name="cdsplice_spawn">%s</attr>' % self.spawn.id
        print >> f, '<attr datatype="Long" name="cdsplice_branch">%i</attr>' % self.branch
        print >>f, '<attr datatype="String" name="cdsplice_command">%s</attr>' % " ".join(sys.argv)

        #Ok done with global atributes now dimensions...
        for d in self.spawn.listdimension():
            D=self.spawn.dimensionobject(d)
            specials = ['units','id','length','bounds','long_name','axis','calendar','partition']
            print >>f,"<axis"
            print >>f,'  datatype = "%s" ' % dataType(D[0])
            for a in specials:
                if a in ["partition",]: # skip these
                    continue
                if a=="length" and D.isTime():
                    continue
                if not hasattr(D,a):
                    continue
                if a=='units' and D.isTime() and self.units!="":
                    A,v = "String",self.units
                else:
                    A,v=dataTypeAndValue(D,a)
                print >>f, '  %s = "%s" ' % (a,v)
            if D.isTime():
                print >>f, 'partition = "[0, %i, %i, %i]"' % (self.branch,self.branch,self.branch+len(self.spawn[tvars[0]].getTime()))
                print >>f, 'name_in_file = "%s"' % D.id
                print >>f, 'length = "%i"' % (len(D)+self.branch)
            elif not hasattr(D,"length"):
                print >>f, '  length = "%i"' % len(D)
            #Ok now other atrributes
            print >> f,">"
            for a in D.attributes:
                if a in specials:
                    continue
                if self.debug:
                    print "looking at att:",a,getattr(D,a)
                A,v=dataTypeAndValue(D,a)
                print >>f, '<attr datatype = "%s" name="%s">%s</attr>' % (A,a,v)
            #now writing dims values
            numpy.set_printoptions(suppress=True)
            numpy.set_printoptions(threshold=1e12)
            if D.isTime():
                if self.units!="":
                    units=self.units
                    D=D.clone()
                    D.toRelativeTime(units,D.getCalendar())
                else:
                    units=D.units
                #Fist we get the time from origin
                T1=self.origin[tvars[0]].getTime().clone()
                T1.toRelativeTime(units,D.getCalendar())
                e1=T1.asComponentTime()[self.branch]
                b2=D.asComponentTime()[0]
                if e1.cmp(b2)>-1:
                    raise Exception,"Original file time of splicing (%s) is in the future of spawned data (%s)"%(e1,b2)
                print >>f, numpy.array(T1[:self.branch].tolist()+D[:].tolist())
            else:
                print >> f,D[:]
            print >>f,"</axis>"
        #At this point all we have left to write are the vars in the file
        for vr in self.spawn.variables:
            V=self.spawn[vr]
            specials = ['id','long_name','units','missing_value']
            print >>f, "<variable"
            op=[]
            for i in range(V.rank()):
                op.append(slice(0,1))
            print >>f, "  datatype = '%s' " % dataType(V(*op))
            for a in specials:
                if not hasattr(V,a):
                    continue
                if self.debug:
                    print "getting:",V.id,a
                A,v=dataTypeAndValue(V,a)
                if v is None:
                    continue
                print >>f, '  %s = "%s" ' % (a,v)
            print >> f,'>'
            for a in V.attributes:
                if a in specials:
                    continue
                A,v=dataTypeAndValue(V,a)
                print >>f, '<attr datatype = "%s" name="%s">%s</attr>' % (A,a,v)
            # Now write domain
            print >>f, "<domain>"
            for a in V.getAxisList():
                print >>f, '<domElem start="0" length="%i" name="%s"/>' % (len(a),a.id)
            print >>f,"</domain>"
            print >> f, "</variable>"
        print >>f,"</dataset>"

    def findBranchTime(self,branch,type):
        """Automatically figures the branch time if not sent"""
        for v in self.origin.variables:
            try:
                t=self.origin[v].getTime()
                break
            except:
                pass
        if self.debug:
            print "ok t is:",t
            print "ORIGIN:",self.origin
            print "V:",v
        bout= None
        if branch is None:
            b = float(self.spawn.branch_time)
            if self.debug:
                print b
        elif type == 'component':
            b = cdtime.s2c(branch)
        elif type=='index':
            bout = int(branch)
            if bout!=float(branch):
                raise RuntimeError,"Index must be int, you passed %s\nDid you mean to pass the type as 'value'" % branch
            if len(t)<=bout:
                raise RuntimeError,"Your start index (%i) is greater than the length of the origin (%i)" % (bout,len(t))
        else:
            b=float(branch)
        if self.debug:
            print "b is",b,self.spawn
        if bout is None: # need to convert value to index
            try:
                print "OK FIRST MAP INTERVAL",t
                bout,e = t.mapInterval((b,b,'ccb'))
                print "FINISHED"
                tc=t.asComponentTime()
                print "WELL:",b,bout,tc
                if self.debug:
                    print b,bout,e,tc[0],tc[-1]
                if e-1 != bout:
                    bout,e, = t.mapInterval((b,b,'cob'))
                    if e-1!=bout:
                        warnings.warn( "Hum something is odd I'm getting more than one index, please report this, command was: %s" % " ".join(sys.argv))
                        if self.debug:
                            print b,bout,e,tc[0],tc[-1]
            except Exception,err:
                print self.origin,err
                raise Exception,"Could not retrieve %s in %s" % (branch,self.origin)
        return bout

