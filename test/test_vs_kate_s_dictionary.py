import cmip5utils

## First get the dictionary of good files
P=cmip5utils.DictParser("data/BIG")

def link_model(model):
    ok = P.get_ok(model)
    for x in ok.keys():
       cmd = "cdsplice.py -s %s -d" % x
       print cmd
    return ok

m = P.ok_models[0]

ok = link_model(m)




