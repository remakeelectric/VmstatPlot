#!/usr/bin/env python
# Karl Palsson, October, 2013, <karlp@remake.is>

import fabric.api as fab
import fabtools as fabt
fab.env.project = "bre-sysstat"

TEMPLATE_UPSTART = """
# Karl Palsson, June 2013, ReMake Electric ehf
author "Karl Palsson <karlp@remake.is>"
description "This is a Fabric managed upstart file for: %(project)s"

start on net-device-up
stop on shutdown

respawn

# You may want to change things like the interface to watch
exec /tmp/%(project)s/sys_stat -O /tmp/%(project)s/output.log -I eth0 %(collect_interval)d

"""


def iupstart():
    """
    Create a verry basic upstart script for running this on Ubuntu machines
    """
    fabt.require.files.template_file(
        path="/etc/init/%(project)s.conf" % fab.env,
        template_contents=TEMPLATE_UPSTART,
        context=fab.env,
        use_sudo=True
    )


def dupstart():
    """Remove our upstart conf"""
    fab.sudo("rm -f /etc/init/%(project)s.conf" % fab.env)


def deploy():
    """
    Install bre-sysstat on a host, and setup service configs
    """
    fabt.require.files.directory("/tmp/%(project)s" % fab.env)
    fabt.require.files.file("/tmp/%(project)s/sys_stat" % fab.env,
        source="sys_stat", mode="775")
    iupstart()


@fab.task
def start(interval=2):
    """
    Install and start gazing at system stats, collecting every interval secs
    """
    fab.env.collect_interval = interval
    deploy()
    fabt.require.service.restarted(fab.env.project)


@fab.task
def stop():
    """
    Stop the collection service and remove all traces of ourself
    """
    fab.run("service %(project)s stop" % fab.env, warn_only=True)
    cleanup()


def cleanup():
    """
    Remove all trace of our code
    """
    fab.run("rm -rf /tmp/%(project)s*" % fab.env)
    dupstart()


@fab.task
@fab.parallel
def _collect(lines):
    fab.env.bre_lines = lines
    # The fab "host" variable might not be a very friendly name
    # as it includes user and port and stuff
    remote_name = fab.run("hostname")
    lines = fab.run("tail -n %(bre_lines)d /tmp/%(project)s/output.log"
                    % fab.env, quiet=True)
    with open("logs/collected-%s-output.log" % remote_name, "w") as f:
        f.write(lines)


@fab.task
@fab.runs_once
def collect(lines=2000):
    """
    Collect the current logs for each machine into a new output directory
    and generate graphs
    """
    fab.local("mkdir -p logs")
    fab.execute(_collect, int(lines))
    fab.local("./graph.sh logs")
    datestr = fab.local("date +%Y-%m-%d.%H%M%S", capture=True)
    fab.local("mv logs logs-%s" % datestr)
    fab.puts("Pretty graphs made in logs-%s/index.html" % datestr)
    showme = fab.prompt("Open a browser to view the graphs?", default="yes")
    if showme.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup']:
        # What? you're not on linux? not really my problem....
        fab.local("xdg-open logs-%s/index.html" % datestr)
