#!/usr/local/uvcdat/latest/bin/python
import sys, getopt
from cmip5utils.splice_dictionary import find_files

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"-s" , ['realm=',\
                                                    'version=',\
                                                    'rip=',\
                                                    'time_frequency=',\
                                                    'experiment=',\
                                                    'tableid=',\
                                                    'variable=',\
                                                    'model=',\
                                                    'root='])

    except getopt.GetoptError:
        print 'Usage: locate_cmip5.py --realm <realm> --version <version>  --rip <rip>'
        sys.exit(2)
    d = {}
    print_search_string = False
    for opt, arg in opts:
        if opt == '-s':
            print_search_string = True
        else:
            key = opt.split("--")[-1]
            d[key] = arg
   
    for x in find_files(d):
        print x
if __name__ == "__main__":
   main(sys.argv[1:])
