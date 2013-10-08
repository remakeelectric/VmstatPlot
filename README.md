VmstatPlot
==========

These are very simple scripts for collecting information about system
load during a load-test, to make it easy to visually identify
bottlenecks by staring at graphs.

At the moment this is a data collector script `sys_stat` which collects
data from `vmstat`, `/proc/` and assorted log files.

The `vmplot.py` script makes it easy to visualize the collected data
using `gnuplot`.

It's somewhat similar to nagios/cacti/mrtg/etc, but instead of focusing
on collecting data every few minutes, and storing and graphing over the
days/months/years timeframe, it uses "vmstat" to collect data at a much
higher rate.  This is particularly useful when doing scalability testing,
where you are running a test that might only take 5-10 minutes.

This runs in two parts, a "daemon" that writes out data to a file, and a
grapher that plots the last X lines of that log file.

### Running locally ###

To start collecting logs, run this on your own system:

    ./sys_stat -O /tmp/some_log_file.txt -I eth0 2

That will include monitoring of eth0 statistics, and collect at a 2 second
interval.

To generate the graphs, run this on your own system:

    tail -500 /tmp/some_log_file.txt | ./vmplot.py -t "graph_title"

That will generate "graph_title.png"

### Running on multiple remote servers ###

It's more interesting of course to run this on the machine(s) you are testing.
A [fabric](http://www.fabfile.org) file is included for running this easily.
(You need fabtools as well as plain fabric at this point in time)

To start collecting:

    fab -H host1,host2,host3 start

To collect and show graphs:

    fab -H host1,host2,host3 collect

To remove all traces of the collection code:

    fab -H host1,host2,host3 stop


## Bugs, quirks, user tweaking ##

* The fabric scripts only target Ubuntu machines at present.
* If your network interfaces aren't eth0, eth1, wlan0 or wlan1, you'll need to edit the COLUMN_MAPPING in vmplot.py
* You need to use the -m <ram size> option to vmplot to get the scaling right for memory usage
* sys_stat needs better help output

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
