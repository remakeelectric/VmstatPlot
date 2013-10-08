#!/bin/bash

# this is currently hardcoded per machine....
# Getting this wrong just makes your graph scales a little off
MACHINE_MEM=512

cd $1
for lf in collected-*-output.log; do
  ../vmplot.py -t $lf -k 1024 -m $MACHINE_MEM $lf
done
ls -1 *.png |sort |sed -e 's/^/<img src="/' -e 's/$/"><br>/' >index.html
cd ..

