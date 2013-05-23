import py7zlib
import genutil
import time
import glob


class Reader(genutil.StringConstructor):
    def __init__(self,template="%(root)/%(experiment)/%(realm)/%(frequency)/%(variable)/cmip5.%(model).%(experiment).%(rip).%(frequency).%(realm).%(variable).%(version).xml",model=None,frequency="mo",realm="atmos",rip="r1i1p1",root="/work/cmip5/",archiveTemplate="%(root)/_archive/%(date)_%(N)_cmip5_xml.7z"):
        self.root=root
        self.archive= genutil.StringConstructor(archiveTemplate)
        self.template = template
        self.rip=rip
        self.realm=realm
        self.frequency=frequency
        self.model=model

    def open(self,variable, date= None, model=None, rip=None, realm=None, frequency=None):
        for s in ["model","rip","realm","frequency"]:
            exec("tmp = %s" % s)
            if tmp is None:
                if getattr(self,s) is None:
                    raise Exception, "You did not define or pass: %s" % s
                exec("%s = self.%s" % (s,s))

        a=open(self.findArchive(date),'rb')
        print a
        A = py7zlib.Archive7z(a)
        nms = A.getnames()
        print nms
        
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


