#!/usr/bin/env python

import cdms2
import os
import sys
import argparse
import numpy
import cmip5utils

parser = argparse.ArgumentParser(description= 'Splices two files together')

parser.add_argument("-o", "--origin",
                    help="Origin (first) file from which spawn was started\nIf not passed, then we will try to figure out the file you're looking for")
parser.add_argument("-s", "--spawn",
                    help="Spawn (second) file will be spliced after the origin file",
                    required=True)
parser.add_argument("-p", "--project",
                    default="CMIP5",
                    help="Project class to be used to try to figure origin file and branch times automagically")
parser.add_argument("-b",
                    "--branch",
                    help="time we want to branch spawn from in source file, i.e LAST valid time in origin")
parser.add_argument("-t", "--type",
                    default='component',
                    choices=['component','index','value'],
                    help="format the branch time was passed as")
parser.add_argument("-x", "--output",
                    help="Output file full path and name\nIf left out then output goes to stdout (screen)",
                    default='screen')
parser.add_argument("-u", "--units",
                    help="Output Units",default="")
parser.add_argument("-D", "--debug",
                    help="Print Debug Messages",default=False,action="store_true")
parser.add_argument("-d","--dryrun",help="Print only, no execution",action="store_true")

args = parser.parse_args(sys.argv[1:])

if args.debug:
    print args
#print args.spawn
   

def loadProject(project,*pargs,**kargs):
    if args.project == "CMIP5":
        if args.debug:
            print "ok we are going here",pargs,kargs
        project = cmip5utils.CMIP5Splicer(*pargs,**kargs)
    else:
        raise RuntimeError,"Only CMIP5 implemented at this point for automation"
    return project

project = None
# figures out the source
project = loadProject(args.project,args.spawn,origin=args.origin,branch=args.branch,type=args.type,output=args.output,units=args.units,debug=args.debug)
spawn = getattr(project.spawn,"uri",project.spawn.id)
origin = getattr(project.origin,"uri",project.origin.id)
branch = project.branch

if args.dryrun:
    print spawn,origin,branch
else:
    project.genXml()

