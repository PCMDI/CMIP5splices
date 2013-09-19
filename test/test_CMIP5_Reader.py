import CMIP5
reload(CMIP5)

import os
if os.uname()[1]=="crunchy.llnl.gov":
    R=CMIP5.Reader()
else:
    R = CMIP5.Reader(root=".",archiveTemplate="./_archives/%(date)_%(N)_cmip5_xml.7z")

print "-%s-" % R.findArchive()
R.model = "CNRM-CM5"

t = R.open("tas")
p = R.open("pr")

