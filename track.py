#!/usr/bin/python
#
# Report changes when a jenkins plugin version has changed
# and there is a corresponding hudson plugin and its
# version is less than the new jenkins version

import subprocess, os, sys, re, shutil
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

def writereport(dict, dir, title):
	shutil.rmtree(dir, True)
	os.makedirs(dir)
	# job checks out code into tracking folder
	# shutil.copyfile('tracking/newspaper.css', dir+'/newspaper.css')
	f = open(dir+'/index.html', 'w')
	print >>f, '<html>'
	print >>f, '<head>'
	print >>f, '<title>'+title+'</title>'
	# print >>f, '<link rel="stylesheet" type="text/css" href="newspaper.css">'
	print >>f, '<style type="text/css">'
	css = open('tracking/newspaper.css')
	for line in css:
		print >>f, line.rstrip()
	css.close()
	print >>f, '</style>'
	print >>f, '</head>'
	print >>f, '<body>'
	if len(dict) == 0:
		print >>f, '<h3>No recent changes</h3>'
	else:
		print >>f, '<table id="newspaper">'
		print >>f, '<caption>'+title+'</caption>'
		print >>f, '<tr>'
		print >>f, '<th>Plugin</th>'
		print >>f, '<th>Hudson Version</th>'
		print >>f, '<th>Jenkins Version</th>'
		print >>f, '</tr>'
		for key in sorted(dict.keys()):
			row = dict[key]
			hversion = row['hversion']
			jversion = row['jversion']
			td = '<td>'
			if cmpversion(hversion, jversion) < 0:
				td = '<td bgcolor="#FFFFCC">'
			if row['hversion'] != 'None':
				print >>f, '<tr>'
				print >>f, td+key+'</td>'
				print >>f, td+hversion+'</td>'
				print >>f, td+jversion+'</td>'
				print >>f, '</tr>'
		print >>f, '</table>'
	print >>f, '</body>'
	print >>f, '</html>'
	f.close()

writereport(changes, 'htmlchanges', 'Recent Plugin Changes')
writereport(status,  'htmlstatus', 'All Hudson Plugins')

if len(changes) > 0:
	print str(len(changes)), 'plugins changed and Jenkins version > Hudson version'
else:
	print 'No plugins changed - job will fail to prevent email'
	os.exit(1)


						
						
					