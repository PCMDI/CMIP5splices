import splice_dictionary as splice
d={}
d["time_frequency"]="mo"
d["experiment"]="rcp*"

bigflag,bigok = splice.flag(d)


import pickle
f = open("BIG_DICTIONARY.dat","w")
pickle.dump(bigflag,f)
f.close()

f = open("BIG_DICTIONARY_ok.dat","w")
pickle.dump(bigok,f)
f.close()
