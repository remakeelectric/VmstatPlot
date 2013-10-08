#!/usr/bin/python
# vmplot.py

#  Generate gnuplot(1) graphs from vmstat(1) output.
#  Copyright (C) 2008  KELEMEN Peter
#  Copyright (C) 2012  Bjarni R. Einarsson
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import optparse
import fileinput
import tempfile
import time

K = 1024
# Map of logfile column names to gnuplot arguments and divider.
# fields labelled "mem:" will have the divider multipled by ram size
COLUMN_MAPPINGS = [
('bi',      '"io:in"       axis x1y2 smooth csplines lt 5 lw 3',   1),
('bo',      '"io:out"      axis x1y2 smooth csplines lt 1 lw 3',   1),
('us',      '"cpu:user"    smooth csplines lt 3 lw 2',             1),
('sy',      '"cpu:sys"     smooth csplines lt 4 lw 1',             1),
('id',      '"cpu:idle"    smooth csplines lt 2 lw 2',             1),
('free',    '"mem:free"    smooth csplines lt 6 lw 2',        10),
('buff',    '"mem:buff"    smooth csplines lt 7 lw 1',        10),
('cache',   '"mem:cache"   smooth csplines lt 8 lw 1',        10),
('swapped', '"mem:swapped" smooth csplines lt 9 lw 2',        10),
('eth0_i',  '"(x100kbit/s) eth0:in"  axis x1y2 smooth csplines lt 5 lw 1', 100 * K),
('eth0_o',  '"(x100kbit/s) eth0:out" axis x1y2 smooth csplines lt 1 lw 1', 100 * K),
('eth1_i',  '"(x100kbit/s) eth1:in"  axis x1y2 smooth csplines lt 5 lw 1', 100 * K),
('eth1_o',  '"(x100kbit/s) eth1:out" axis x1y2 smooth csplines lt 1 lw 1', 100 * K),
('wlan0_i', '"(x5kbit/s) wlan0:in"  axis x1y2 smooth csplines lt 5 lw 1', 5 * K),
('wlan0_o', '"(x5kbit/s) wlan0:out" axis x1y2 smooth csplines lt 1 lw 1', 5 * K),
('wlan1_i', '"(x5kbit/s) wlan1:in"  axis x1y2 smooth csplines lt 5 lw 1', 5 * K),
('wlan1_o', '"(x5kbit/s) wlan1:out" axis x1y2 smooth csplines lt 1 lw 1', 5 * K),
('syslog',  '"(LPS) syslog" axis x1y2 lt 2 lw 1',                       10),
('http_req', '"(QPS) http_req" axis x1y2 lt 3 lw 1',                     10),
('http_err', '"(QPSx100) http_err" axis x1y2 lt 1 lw 2',                0.1),
]


iocols = ['bi', 'bo']   # this might be Linux-specific...
index = {}      # index of columns corresponding to header fields
sums = {}       # sum of columns corresponding to header fields in iocols
pcnts = {}      # count of positive values corresponding to header fields in iocols
avgs = {}       # average of columns corresponding to header fields in iocols
lc = 0          # line count

def build_column_index(x):
    for i in xrange(len(x)):
        index[x[i]] = i
        sums[x[i]] = 0
        pcnts[x[i]] = 0
    for i in iocols:
        if i not in x:
            print 'What you gave me does not seem to be vmstat(1) output, exiting.'
            sys.exit(10)
    print "column index built at line", lc

parser = optparse.OptionParser()
parser.add_option("-t", "--title", default=os.path.basename(os.getcwd()), help="graph title")
parser.add_option("-e", "--email", default=None, help="graph author email address")
parser.add_option("-c", "--timecol", default=20, help="column with current time")
parser.add_option("-k", "--kilobytes", default=0, help="throughput axis scale")
parser.add_option("-m", "--ram", default=4096, help="megabytes of RAM available")
parser.add_option("-p", "--postscript", action="store_true", default=False, help="additional PostScript graph output")
parser.add_option("-r", "--retain", action="store_true", default=False, help="retain temporary files")
parser.add_option("-4", "--slc4", action="store_true", default=False, help="SLC4 (gnuplot 4.0) compatibility")
(options, args) = parser.parse_args()

print "option: title =", options.title
print "option: email =", options.email
print "args: %s" % args

try:
    options.timecol = int(options.timecol)
except:
    print "E: Invalid number. (%s)" % options.timecol
    sys.exit(1)
print "option: timecol =", options.timecol

try:
    options.ram = int(options.ram)
except:
    print "E: Invalid number. (%s)" % options.ram
    sys.exit(1)
print "option: ram =", options.ram

try:
    options.kilobytes = int(options.kilobytes)
except:
    print "E: Invalid number. (%s)" % options.kilobytes
    sys.exit(1)
print "option: kilobytes =", options.kilobytes

print "option: postscript =", options.postscript

outlines = []
for line in fileinput.input(args):
    if 'procs' in line:
        continue
    cols = line.split()
    if not index and 'free' in cols:
        build_column_index(cols)
        continue
    if index and cols[1].isdigit():
        skip = False
        for i in iocols:
            if cols[index[i]].isdigit():
                x = int(cols[index[i]])
                if x == 0:
                    continue
                if x < 10**9:   # skip vmstat(1) overflow errors
                    sums[i] = sums[i] + x
                    pcnts[i] = pcnts[i] + 1
                else:
                    print x, "too large, skipping"
                    skip = True
            else:
                print '%s:%u: column %u is garbled: "%s", skipping' % (
                fileinput.filename(),
                fileinput.filelineno(),
                index[i],
                cols[index[i]])
                skip = True
        if not skip:
            outlines.append(line)
            lc += 1

# This tries to remove most of the time stamps, so the X axis isn't
# too crowded (And offset them a little from the origin)
# We do this after processing all lines so we don't have to be told in advance
# how many lines are in the file
vmstat = tempfile.mkstemp('.tmp', 'vmplot-vmstat-')
if options.retain:
    print "sanitized vmstat file:", vmstat[1]

for i, l in enumerate(outlines):
    if i % (lc / 5) != 5:
        time_field = l.split()[options.timecol - 1]
        l = l.replace(time_field, "''")
    os.write(vmstat[0], l)
os.close(vmstat[0])

options.label = time.strftime("%F %T", time.localtime())
if options.email:
  options.label = options.email + ' ' + options.label

plot = []
if options.slc4:
  plot.append('set terminal png small;')
  plot.append('set size 1.6,1.0;')
else:
  plot.append('set terminal png small size 1024,480 ;')
  plot.append('set label "%s" front offset -11,-2.5 ;' % (options.label))

plot.append('set output "%s.png";' % options.title)
plot.append('set title "%s";' % options.title)
plot.append('set key below;')
plot.append('set xlabel "Time";')
plot.append('set y2label "I/O (KB/s)";')
plot.append('set y2tics nomirror;')
if options.kilobytes: plot.append('set y2range [0:%d];' % options.kilobytes)
plot.append('set yrange [0:103];')
plot.append('set ylabel "Memory/CPU utilization (%)";')
plot.append('set ytics 20;')
plot.append('set grid linetype 0;')

if options.timecol > 0:
  plots = [('"%s" using 0:%d:xtic(%d) axis x1y2 title "t" lt 7 lw 0'
            ) % (vmstat[1], options.timecol, options.timecol)]
else:
  plots = []

for col, args, div in COLUMN_MAPPINGS:
  if col in index:
    if "mem:" in args:
      div = div * options.ram
    plots.append('"%s" using 0:($%d/%s) title %s' % (vmstat[1], 1+index[col],
                                                     div, args))
plot.append('plot %s;' % ', '.join(plots))

if options.postscript:
  plot.append('set terminal postscript color landscape small;')
  plot.append('set size 1.0,1.0;')
  plot.append('set output "%s.ps";' % options.title)
  plot.append('replot;')

gnuplot = tempfile.mkstemp('.tmp', 'vmplot-gnuplot-')
if options.retain:
    print "gnuplot command file:", gnuplot[1]
os.write(gnuplot[0], '\\\n'.join(plot))
os.close(gnuplot[0])

os.system('gnuplot %s' % gnuplot[1])

if not options.retain:
    os.remove(vmstat[1])
    os.remove(gnuplot[1])

# End of file.
