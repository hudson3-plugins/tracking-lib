#!/usr/bin/python
#
# Compare hudson and jenkins update centers and extract summaries
# for further processing.
#
# Adapted from track.py. 

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

scms = {
	'github.com':
		{ 'scm': 'git', 'clone': 'git clone https://github.com/jenkinsci/{0}-plugin.git' },
	'svn.dev.java.net':
		{ 'scm': 'svn', 'clone': 'svn co https://svn.jenkins-ci.org/trunk/hudson/plugins/{0}/' },
	'bitbucket.org':
		{ 'scm': 'git', 'clone': 'hg clone https://bitbucket.org/henriklynggaard/{0}-plugin' },
	'svn.jenkins-ci.org':
		{ 'scm': 'svn', 'clone': 'svn co https://svn.jenkins-ci.org/trunk/hudson/plugins/{0}/' },
	'svn.java.net':
		{ 'scm': 'svn', 'clone': 'svn co https://svn.jenkins-ci.org/trunk/hudson/plugins/{0}/' },
	'hudson.dev.java.net':
		{ 'scm': 'svn', 'clone': 'svn co https://svn.jenkins-ci.org/trunk/hudson/plugins/{0}/' },
	'build-pipeline-plugin.googlecode.com':
		{ 'scm': 'hg', 'clone': 'hg clone https://code.google.com/p/{0}/' }
}
scmexceptions = {
	"assembla-auth": {
		"scm": "git",
		"clone": "git clone git://git.assembla.com/assembla-oss.jenkins-auth.git"
	}
}

extract = {}
notinhudson = []
notinjenkins = []
olderinhudson = []

for key, jplugin in jplugins.items():
	jversion = jplugin['version']
	hplugin = hplugins.get(key, None)
	extract[key] = ex = {}
	ex['version'] = jversion
	ex['url'] = jplugin['url']
	scmcode = jplugin['scm']
	scm = scms.get(scmcode, None)
	if not scm:
		scm = scmexceptions.get(key, None)
	if scm:
		ex['scm'] = scm['scm']
		ex['clone'] = scm['clone']
	else:
		ex['scm'] = 'Unknown'
	ex['diff'] = 'Same'
	if not hplugin:
		ex['diff'] = 'Missing'
		notinhudson.append(key)
	if hplugin and cmpversion(hplugin['version'], jversion) < 0:
		ex['diff'] = 'Older'
		olderinhudson.append(key)

for key, hplugin in hplugins.items():
	if not jplugins.get(key, None):
		# We have already added all the hudson/jenkins pairs
		notinjenkins.append(key)

dumpAsJson('extract.json', extract)
dumpAsJson('notinhudson.json', notinhudson)
dumpAsJson('notinjenkins.json', notinjenkins)
dumpAsJson('olderinhudson.json', olderinhudson)

print ' '+str(len(notinjenkins)), 'hudson plugins not in jenkins'
print str(len(hplugins)-len(olderinhudson)-len(notinjenkins)), 'hudson plugins up to date'
print str(len(olderinhudson)), 'hudson plugins older version'
print str(len(notinhudson)),  'jenkins plugins not in hudson'
print str(len(notinhudson)+len(olderinhudson)), 'jenkins plugins to convert'
						
					