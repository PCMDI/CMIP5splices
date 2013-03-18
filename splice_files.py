import cdms2 as cdms
import splice_dictionary as splice
import cdtime
import sys, getopt
import MV2 as MV
import cdutil,genutil
import numpy as np

cdms.setNetcdfShuffleFlag(0)
cdms.setNetcdfDeflateFlag(0)
cdms.setNetcdfDeflateLevelFlag(0)

def splice_files(argv):
    #Parse the command line arguments
    try:
        opts, args = getopt.getopt(argv,"-f" , ['realm=',\
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

    #-f option prints flagged files to FLAG.txt  Other options populate dictionary keys
    d = {}
    list_flagged_files = False
    for opt, arg in opts:
        if opt == '-f':
            list_flagged_files = True
        else:
            key = opt.split("--")[-1]
            d[key] = arg
    print d


    #Get the flagged and OK files
    flagged, ok = splice.flag(d)

    #Loop over files that passed initial test

    for rcp in ok.keys():

        historical = ok[rcp]

         #get attributes based on historical and rcp filenames/
        hist_dict = splice.parse_filename(historical)
        rcp_dict = splice.parse_filename(rcp)
        variable = hist_dict["variable"]
        experiment = "hist_"+rcp_dict["experiment"]
        version = hist_dict["version"] + "+"+rcp_dict["version"]


        #The historical files should span 1979-2005
        hist_start = cdtime.comptime(1979,1,1)
        hist_stop = cdtime.comptime(2005,12,31)

        #spliced files should span 2006-2011
        rcp_start = cdtime.comptime(2006,1,1)
        rcp_stop = cdtime.comptime(2011,12,31)

        #get historical data
        hist_file = cdms.open(historical)
        hist_data = hist_file(variable,time=(hist_start,hist_stop))
        hist_file.close()
       
        #get rcp data
        rcp_file = cdms.open(rcp)
        rcp_data = rcp_file(variable,time=(rcp_start , rcp_stop))
        rcp_file.close()

        #set up a new spliced time axis.  
        hist_times = hist_data.getTime()
        rcp_times = rcp_data.getTime()
        st = hist_times.asComponentTime()+rcp_times.asComponentTime()
        units = hist_times.units
        calendar = hist_times.getCalendar()
        st = [x.torel(units,calendar).value for x in st]
        spliced_time = cdms.createAxis(st)
        spliced_time.id = "time"
        spliced_time.units = hist_times.units
        spliced_time.designateTime()

        #create a new variable to hold spliced data.  .
        spliced = MV.zeros((len(spliced_time), hist_data.shape[1],hist_data.shape[2]))
        spliced[:hist_data.shape[0]]=hist_data
        spliced[hist_data.shape[0]:hist_data.shape[0]+rcp_data.shape[0]]=rcp_data
        spliced.id = hist_data.id
        spliced.name = hist_data.name
        spliced.units = hist_data.units

        #Set appropriate axes
        spliced.setAxis(0,spliced_time)
        spliced.setAxis(1,hist_data.getAxis(1))
        spliced.setAxis(2,hist_data.getAxis(2))
        
       
        #determine write path and write filename
        path = "/export/marvel1/SeaIce/SPLICED/"+experiment+"/"+variable+"/"
        splicefile = historical.split("/")[-1].replace("historical","spliced")
        splicefile = splicefile.replace(hist_dict["version"],version)
        splicefile = splicefile.replace("xml","nc")

        #write the file
        writefile = cdms.open(path+splicefile,"w")
        writefile.write(spliced)
        writefile.close()



if __name__ == "__main__":
   splice_files(sys.argv[1:])

    
                                   
    
    
    
    
