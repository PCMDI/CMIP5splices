import CMIP5
R = CMIP5.Reader(root=".",archiveTemplate="./_archives/%(date)_%(N)_cmip5_xml.7z")

print "-%s-" % R.findArchive()
R.model = "CNRM-CM5"

print R.open("tas")
