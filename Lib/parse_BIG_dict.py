import splice_dictionary as splice
import pickle
import numpy as np
from collections import Counter
import csv


class Parser():
    def __init__(self,name="BIG_DICTIONARY"):
        f = open("%s.dat" % name,"r")
        self.bigflag = pickle.load(f)
        f.close()
        
        f = open("%s_ok.dat" % name,"r")
        self.bigok = pickle.load(f)
        f.close()
        
        ## get rcp runs only ##
        self.ok = {}
        self.flag = {}
        rcp_index = np.where([x.split(".")[2].find("rcp")>=0 for x in self.bigflag.keys()])[0]
        for k in np.array(self.bigflag.keys())[rcp_index]:
            self.flag[k]=self.bigflag[k]

        rcp_index_ok = np.where([x.split(".")[2].find("rcp")>=0 for x in self.bigok.keys()])[0]
        
        for k in np.array(self.bigok.keys())[rcp_index_ok]:
            self.ok[k]=self.bigok[k]
        
        self.flagged_models = np.array([k.split(".")[1] for k in self.flag.keys()])
        self.ok_models = np.array([k.split(".")[1] for k in self.ok.keys()])


    def get_ok(self,model):
        d = {}
        Iok = np.where([x==model for x in self.ok_models])[0]
        for k in  np.array(self.ok.keys())[Iok]:
            d[k] = self.ok[k]
        return d

    def get_flagged(self,model):
        d={}
        Iflag = np.where([x==model for x in self.flagged_models])[0]
        for k in np.array(self.flag.keys())[Iflag]:
            d[k] = self.flag[k]
        return d

    def write_realm(self):
        csvfile = open("Metadata_errors_realms.csv","wb")
        csvwriter = csv.writer(csvfile)
        fkeys =Counter([x.split(".")[6] for x in self.flag.keys()]).keys()
        okkeys=Counter([x.split(".")[6] for x in self.ok.keys()]).keys()
        realms = sorted(Counter(fkeys+okkeys).keys())
        
        header = ["MODEL","flag"]+ realms
        
        csvwriter.writerow(header)
        
        C = Counter(self.flagged_models)
        Citer = iter(C.most_common())

        for model, num in Citer:
            problem_dict = self.get_flagged(model)
            l = []
            for k in problem_dict.keys():
                for prob in problem_dict[k]:
                    l.append(prob)
            flags = Counter(l)
            for badness,num in iter(flags.most_common()):
                BadnessCount = Counter([k.split(".")[6] if badness in problem_dict[k] else None for k in problem_dict.keys()])
                realm_bad = [BadnessCount[x] for x in realms]
                csvwriter.writerow([model,badness]+realm_bad)
        csvfile.close()

    #def check(self,model):
     #   flag = self.get_flagged(model)
      #  ok = self.get_ok(model)
       # rcp_index = np.where([x.split(".")[2].find("rcp")>=0 for x in flag])
       # if len(rcp_index) !=0:
        #    keys = flag[rcp_index]
         #   return keys
