#!/bin/bash

# this is currently hardcoded per machine....
# Getting this wrong just makes your graph scales a little off
MACHINE_MEM=512

cd $1
for lf in *app*.log; do
  ../vmplot.py -t $lf -c 21 -k 1024 -m 4096 $lf
done
for lf in *lb*.log *db*log; do
  ../vmplot.py -t $lf -c 21 -k 1024 -m 2048 $lf
done
ls -1 *.png |sort |sed -e 's/^/<img src="/' -e 's/$/"><br>/' >index.html
cd ..

