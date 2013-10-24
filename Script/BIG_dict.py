#!/usr/bin/env python
import cmip5utils.splice_dictionary as splice
import argparse
import sys

parser = argparse.ArgumentParser(description= 'Generate BIG_DICTIONARY files')
parser.add_argument("-e", "--experiment",default="rcp*")
parser.add_argument("-f", "--time_frequency",default="mo")
parser.add_argument("-v", "--variable",default=None)
parser.add_argument("-r", "--realm",default=None)
parser.add_argument("-m", "--model",default=None)
parser.add_argument("-R", "--rip",default=None)
parser.add_argument("-V", "--version",default=None)
parser.add_argument("-t", "--table_id",default=None)
parser.add_argument("-l", "--latest",default=None)
parser.add_argument("-o", "--output",default="data/BIG_DICTIONARY")

p = parser.parse_args(sys.argv[1:])
d={}
for kw in p._get_kwargs():
    if kw[1] is not None:
        d[kw[0]]=kw[1]

bigflag,bigok = splice.flag(d)


import pickle
f = open("%s.dat" % p.output,"w")
pickle.dump(bigflag,f)
f.close()

f = open("%s_ok.dat" % p.output,"w")
pickle.dump(bigok,f)
f.close()
