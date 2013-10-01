import cmip5utils

## First get the dictionary of good files
P=cmip5utils.DictParser("data/BIG")
bad = P.get_flagged("CNRM-CM5")
good = P.get_ok("MIROC5")

print good
print bad


