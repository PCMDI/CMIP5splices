import sys
import cdms2
import numpy

#Create test datasets
a=numpy.arange(10,100)
b=numpy.arange(50,150)

d1=cdms2.MV2.array(2.*a)
d2=cdms2.MV2.array(3.*b)

t1=cdms2.createAxis(a)
t1.designateTime()
t1.id='time'
t1.units='days since 2013'

t2=cdms2.createAxis(b)
t2.designateTime()
t2.id='time'
t2.units='days since 2013'


d1.setAxis(0,t1)
d2.setAxis(0,t2)
f=cdms2.open('2x.nc','w')
f.write(d1,id='y')
f.close()

f=cdms2.open('3x.nc','w')
f.write(d2,id='y')
f.branch_time=20
f.experiment_id = "3x"
f.parent_experiment_id="2x"
f.realization=1
f.initialization_method=1
f.physics_version=1
f.parent_experiment_rip="r1i1p1"
f.close()

print "Start times:", t1.asComponentTime()[0], t2.asComponentTime()[0]
#Now run a few test
import os
def test(index,value):
    f1=cdms2.open("test1.xml")
    y=f1("y")
    try:
        assert(y[index]==value)
    except:
        print "failed test"
        sys.exit()

cmd = "%s Script/cdsplice.py -s 3x.nc -o 2x.nc -x test1.xml"%sys.executable
print cmd
f1 = os.popen(cmd).readlines()
test(10,150.)
test(9,38.)

cmd = "%s Script/cdsplice.py -t index -b 23 -s 3x.nc -o 2x.nc -x test1.xml"%sys.executable
print cmd
f1 = os.popen(cmd).readlines()
test(23,150.)
test(22,64.)

cmd = "%s Script/cdsplice.py -b 2013-2-12 -s 3x.nc -o 2x.nc -x test1.xml"%sys.executable
print cmd
f1 = os.popen(cmd).readlines()
test(31,82)
test(32,150)

cmd = "%s Script/cdsplice.py -b 23 -t value -s 3x.nc -o 2x.nc -x test1.xml"%sys.executable
print cmd
f1 = os.popen(cmd).readlines()
test(12,44)
test(13,150)

cmd = "%s Script/cdsplice.py -s 3x.nc  -x test1.xml"%sys.executable
print cmd
f1 = os.popen(cmd).readlines()
test(9,38)
test(10,150)

cmd = "%s Script/cdsplice.py -u 'days since 1780' -s 3x.nc  -x test1.xml"%sys.executable
print cmd
f1 = os.popen(cmd).readlines()
test(9,38)
test(10,150)
y=cdms2.open("test1.xml")("y")
t=y.getTime()
assert(t[9]==85121)
assert(t[10]==85152)


