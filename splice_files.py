import cdms2
import os
import splice_dictionary
import cdtime
import sys
import argparse
import datetime
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

def splice_files(argv):
    parser = argparse.ArgumentParser(description="splice two files")
    parser.add_argument('--realm')
    parser.add_argument('--version')
    parser.add_argument('--rip')
    parser.add_argument('--time_frequency')
    parser.add_argument('--experiment')
    parser.add_argument('--tableid')
    parser.add_argument('--variable')
    parser.add_argument('--model')
    parser.add_argument('--root')
    parser.add_argument('--dictionary')
    parser.add_argument('--runflag',action='store_true')
    parser.add_argument('--f',action='store_true')
    parser.add_argument('--out',help='Directory to dump output to',default="/export/marvel1/SPLICED/")
    #Parse the command line arguments
    args = parser.parse_args(argv)
    #-f option prints flagged files to FLAG.txt  Other options populate dictionary keys
    d = {}
    list_flagged_files = False
    for k, v in args._get_kwargs():
        if k=='f':
            list_flagged_files = v
        elif k=='dictionary':
            if v is None:
                args.dictionary = 'flagged.dict'
        elif k == 'runflag':
            pass
        elif v is not None:
            d[k] = v
    #print d


    
    #Get the flagged and OK files
    if args.runflag is False and not os.path.exists(args.dictionary):
        args.runflag = True
    if args.runflag:
        flagged, ok = splice_dictionary.flag(d)
        f=open(args.dictionary,'w')
        f.write(repr((flagged,ok)))
        f.close()
    else:
        f=open(args.dictionary)
        
        flagged,ok = eval(f.read())

        f.close()
        
    #Loop over files that passed initial test
    print ok.keys()
    for rcp in ok.keys():
        print rcp
        historical = ok[rcp]

         #get attributes based on historical and rcp filenames/
        hist_dict = splice_dictionary.parse_filename(historical)
        rcp_dict = splice_dictionary.parse_filename(rcp)
        variable = hist_dict["variable"]
        experiment = "hist_"+rcp_dict["experiment"]
        version = hist_dict["version"] + "+"+rcp_dict["version"]


        #The historical files should span 1979-2005
        hist_start = cdtime.comptime(1979,1,1)
        hist_stop = cdtime.comptime(2005,12,31)

        #spliced files should span 2006-present
        
        rcp_start = cdtime.comptime(2006,1,1)
        time_now = datetime.datetime.now()
        rcp_stop = cdtime.comptime(time_now.year,time_now.month,time_now.day)

        #get historical data time axis
        hist_file = cdms2.open(historical)
        hist_data = hist_file[variable]
        try:
            hist_times = hist_data.getTime().clone()
        except:
            print "Couldn't clone "+historical
            continue
        h1,h2 = hist_times.mapInterval((hist_start,hist_stop))
        hist_times = hist_times.subAxis(h1,h2)

        #get rcp data
        rcp_file = cdms2.open(rcp)
        rcp_data = rcp_file[variable]
        try:
            rcp_times=rcp_data.getTime().clone()
        except:
            print "Couldn't clone "+rcp
            continue
        r1, r2 = rcp_times.mapInterval((rcp_start , rcp_stop))
        rcp_times=rcp_times.subAxis(r1,r2)

        #set up a new spliced time axis.  
        st = hist_times.asComponentTime()+rcp_times.asComponentTime()
        units = hist_times.units
        calendar = hist_times.getCalendar()
       
        st = [x.torel(units,calendar).value for x in st]
        spliced_time = cdms2.createAxis(st)
        spliced_time.id = "time"
        spliced_time.units = hist_times.units
        spliced_time.designateTime()
        spliced_time.setCalendar(calendar)

        #determine write path and write filename
        path = os.path.join(args.out,experiment,variable)
        splicefile = historical.split("/")[-1].replace("historical","spliced")
        splicefile = splicefile.replace(hist_dict["version"],version)
        splicefile = splicefile.replace("xml","nc")

        #write the file
        fout = os.path.join(path,splicefile)
        try:
            os.makedirs(os.path.dirname(fout))
        except:
            pass
        writefile = cdms2.open(fout,"w")


        #create a new variable to hold spliced data.  .
        # Ok hist times
        ntimes = 12 # 1 year at a time
        j=0
        for i in range(h1,h2,ntimes):
            m = min(h2,i+ntimes)
            #print "hist:",i,m
            tmp = hist_data(time=slice(i,m))
            tmp.setAxis(0,spliced_time.subAxis(j,j+m-i))
            writefile.write(tmp)
            j+=m-i
        # Ok same for rcp
        #Set appropriate axes
        for i in range(r1,r2,ntimes):
            m = min(r2,i+ntimes)
            
            #print "rcp:",i,m
            tmp = rcp_data(time=slice(i,m))
            tmp.setAxis(0,spliced_time.subAxis(j,j+m-i))
            writefile.write(tmp)
            j+=m-i
        
       
        writefile.close()

if __name__ == "__main__":
   splice_files(sys.argv[1:])

    
                                   
    
    
    
    
