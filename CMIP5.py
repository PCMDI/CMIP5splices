import py7zlib
import genutil
import time
import glob
import subprocess

class A7z(object):
    def __init__(self,file,za="/work/cmip5/_archive/7za"):
        self.za = za
        self.file = file
    def getnames(self):
        cmd = (self.za,"l",self.file)
        o = subprocess.check_output(cmd)
        return o
    def getmembers(self,member,extract=False):
        if extract:
            option = "e"
        else:
            option = "l"
        cmd = (self.za,option,"-y",self.file,member)
        if extract:
            subprocess.call(cmd)
        else:
            o = subprocess.check_output(cmd)
        return o

class Reader(genutil.StringConstructor):
    def __init__(self,template="%(experiment)/%(realm)/%(frequency)%(new)/%(variable)/cmip5.%(model).%(experiment).%(rip).%(frequency).%(realm).%(variable).%(version).xml",model=None,experiment='1pctCO2',frequency="mo",realm="atmos",rip="r1i1p1",root="/work/cmip5/",archiveTemplate="%(root)/_archive/%(date)_%(N)_cmip5_xml.7z"):
        self.root = root
        self.archive = genutil.StringConstructor(archiveTemplate)
        self.template = genutil.StringConstructor(template)
        self.rip = rip
        self.realm = realm
        self.experiment = experiment
        self.frequency = frequency
        self.model = model
        self.archives = {}

    def open(self,variable, date= None, model=None, experiment=None, rip=None, realm=None, frequency=None):
        for s in ["experiment","model","rip","realm","frequency"]:
            exec("tmp = %s" % s)
            if tmp is None:
                if getattr(self,s) is None:
                    raise Exception, "You did not define or pass: %s" % s
                exec("self.template.%s = self.%s" % (s,s))
            else:
                exec("self.template.%s = %s" % (s,tmp))

        anm = self.findArchive()
        print "Archive:",anm,time.time()
        A = A7z(anm)
        print dir(A),time.time()
        nms = A.getnames()
        self.template.variable=variable
        self.template.version="*"
        possible_names = self.template()
        possibles = A.getmembers(possible_names)
        print possibles
        return A
        
    def findArchive(self,date=None):
        if date is None:
            now = time.localtime()
            date = "%.2i%.2i%.2i" % (now.tm_year-2000, now.tm_mon, now.tm_mday)
        elif isinstance(date,int):
            date =str(date)
        for k in self.archive.keys():
            setattr(self.archive,k,"*")
        self.archive.root = self.root
        files = glob.glob(self.archive())
        dates = []
        for f in files:
            try:
                dic = self.archive.reverse(f)
            except Exception,err:
                continue
            D = dic["date"]
            if D == date:
                return f
            dates.append(int(D))
        dates.sort()
        date=int(date)
        r=dates[0]
        for D in dates:
            if date>D:
                r = D
        self.archive.date=str(r)
        return glob.glob(self.archive())[0]


