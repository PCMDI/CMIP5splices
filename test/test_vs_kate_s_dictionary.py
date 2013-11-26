import cmip5utils,sys,genutil,os,glob,subprocess,shlex,cdms2,cdtime
nm = sys.argv[1]

## First get the dictionary of good files
P=cmip5utils.DictParser("data/%s" % nm)

template = genutil.StringConstructor(cmip5utils.splice_dictionary.defaultTemplate)

def link_model(model,bad=False):
    if not bad:
        ok = P.get_ok(model)
        print P.ok_models
    else:
        ok = P.get_flagged(model)
        print "Bad ones for %s: %s" % (model,ok)
        print P.flagged_models
    gened = []
    for x in ok.keys():
        template.root = "/".join(os.path.dirname(x).split("/")[:-4])+"/"
        sp = os.path.split(x)[1].split(".")
        template.model=sp[1]
        template.experiment=sp[2]
        template.rip=sp[3]
        template.time_frequency=sp[4]
        template.realm=sp[5]
        template.tableid=sp[6]
        template.variable=sp[7]
        template.version=sp[8]
        template.latest=sp[9]
        # ok now we need to figure the best possible (latest) historical
        exp = template.experiment # saving for later
        ver = template.version
        template.experiment="historical"
        template.version="*"
        possible = glob.glob(template())
        good_hist = cmip5utils.splice_dictionary.newest_version(possible)
        # Now construct output name
        template.experiment="historical-%s" % exp
        template.version = ver
        out = template()
        gened.append(out)
        if os.path.exists(out):
            print "Output: %s already here, skipping" % (out)
        else:
            root = os.path.dirname(out)
            if not os.path.exists(root):
                os.makedirs(root)

            ## Because branch time is soooo messed up we are actually going to manually splice it from one month before rcp starts
            f=cdms2.open(x)
            for v in f.variables.values():
                if v.getTime() is not None:
                    tc=v.getTime().asComponentTime()[0]
                    tc=tc.sub(30,cdtime.Day)
                    break

            cmd = "cdsplice.py -s %s -o %s -x %s -b '%s' --type=component" % (x,good_hist,out,tc)
            print cmd
            p = subprocess.Popen(shlex.split(cmd),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            p.wait()
            if not os.path.exists(out):
                print "Could not generate: %s" % (out)
            else:
                print "Success for %s" % (out)

    return ok,gened

G=[]
print "OK MODELS:",P.get_ok_models()

for m in P.get_ok_models():
    try:
      ok,g = link_model(m)
      G+=g
    except Exception,err:
        print err
        pass
print "Finished:",len(G), len(set(G))

#Ok now some "bad" models that we decide to run anyway
bad_but_we_still_want = ["CCSM4",]
for b in bad_but_we_still_want:
    print "Bad model:",b
    try:
      ok,g = link_model(b,bad=True)
      G+=g
    except Exception,err:
        print "Failed",b,err
        pass

