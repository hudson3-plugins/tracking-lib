#!/usr/bin/python
#
# Report changes when a jenkins plugin version has changed
# and there is a corresponding hudson plugin and its
# version is less than the new jenkins version

import subprocess, os, sys, re
from json_files import *
from read_update_center import *
from cmpversion import *

def read_plugins(url, who):
	plugins = read_update_center(url)['plugins']
	if not plugins:
		print "Can't read", who, "update center"
		sys.exit(1)
	return plugins

jplugins = read_plugins("http://updates.jenkins-ci.org/update-center.json", 'jenkins')
hplugins = read_plugins("http://hudson-ci.org/update-center3/update-center.json", 'hudson')

print str(len(jplugins)), 'plugins in jenkins update center'
print str(len(hplugins)), 'plugins in hudson  update center'

status = loadFromJson('status.json')
if not status:
	status = {}

changes = {}
defaulthplugin = {}
defaultjplugin = {}

for key, jplugin in jplugins.items():
	jversion = jplugin['version']
	hplugin = hplugins.get(key, None)
	splugin = status.get(key, None)
	if hplugin and (not splugin or not splugin.get('jversion', None) or cmpversion(splugin['jversion'], jversion) != 0):
		hversion = hplugin['version']
		if cmpversion(hversion, jversion) < 0:
			# this is a reportable change!
			changes[key] = change = {}
			change['hversion'] = hversion
			change['jversion'] = jversion	
	status[key] = stat = {}
	stat['jversion'] = jversion
	if hplugin:
		stat['hversion'] = hplugin['version']
	else:
		stat['hversion'] = 'None'

for key, hplugin in hplugins.items():
	if not jplugins.get(key, None):
		# We have already added all the hudson/jenkins pairs
		status[key] = stat = {}
		stat['hversion'] = hplugin['version']
		stat['jversion'] = 'None'

dumpAsJson('changes.json', changes)
dumpAsJson('status.json', status)

print str(len(changes)), 'plugins changed and Jenkins version > Hudson version'
					
						
					