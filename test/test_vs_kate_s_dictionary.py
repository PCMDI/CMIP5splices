import cmip5utils,sys,genutil,os,glob,subprocess,shlex
nm = sys.argv[1]

## First get the dictionary of good files
P=cmip5utils.DictParser("data/%s" % nm)

template = genutil.StringConstructor(cmip5utils.splice_dictionary.defaultTemplate)

def link_model(model):
    ok = P.get_ok(model)
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
        root = os.path.dirname(out)
        if not os.path.exists(root):
            os.makedirs(root)
        cmd = "cdsplice.py -s %s -o %s -x %s" % (x,good_hist,out)
        print cmd
        p = subprocess.Popen(shlex.split(cmd),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p.wait()
    return ok

for m in P.ok_models:
    try:
      ok = link_model(m)
    except:
        pass



