#!/usr/bin/python
import subprocess, errno, sys, re, os
import urllib, shutil
from json_files import *
from read_update_center import *
from utils import *

if len(sys.argv) != 3:
	print 'Usage: ./load_test_hudson.py HUDSON_WAR_PATH PLUGIN_NAME'

pluginname = sys.argv[2]

hplugins = read_plugins("http://hudson-ci.org/update-center3/update-center.json")

print str(len(hplugins)), 'plugins in hudson3 update center'

freshdir('plugin')

rename = re.compile('/([-_a-zA-Z0-9]*\.hpi)')

info = hplugins.get(pluginname, None)
if not info:
	print "Plugin", pluginname, "not found in update center"
	sys.exit(1)
version = info['version']

#
# Collect recursive dependencies for plugin and its dependencies
#

def getdependencies(plugin):
	value = hplugins.get(plugin, None)
	if not value:
		print "Can't find plugin", plugin
		sys.exit(1)
	deps = value['dependencies']
	depends = set()
	for dep in deps:
		depname = dep.get('name', None)
		# null in json file seems to be translated to 'null'
		if depname and not depname == 'null' and not dep['optional']:
			depends.add(depname)
	return depends

print "Calculate recursive dependencies"

def finddeps(plugin, allset):
	allset.add(plugin)
	depends = getdependencies(plugin)
	for dep in depends:
		if dep not in allset:
			finddeps(dep, allset)

all = set()
finddeps(pluginname, all)
dependset = all

print "Load plugin and dependencies"

#
# Load test plugin with its dependencies in otherwise empty hudson_home
#

print "Load plugins in Hudson"

home = {'HUDSON_HOME': './hudson_home'}
run = ['java', '-jar', sys.argv[1], '--httpPort=18080', '--skipInitSetup']
refailed = re.compile(r"SEVERE: Failed Loading plugin ([-_a-zA-Z0-9]*)")

rename = re.compile('/([-_a-zA-Z0-9]*\.hpi)')

freshdir('hudson_home')
cmds('mkdir hudson_home/plugins')

for dep in dependset:
	value = hplugins.get(dep, None)
	if not value:
		print "Plugin", dep, "not found in hudson central"
		sys.exit(1)
	url = value['url']
	match = re.search(rename, url)
	if not match:
		print "Can't find hpi name in", url
		sys.exit(1)
	urllib.urlretrieve(url, 'hudson_home/plugins/'+match.group(1))
		
p = subprocess.Popen(run, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=home)
lines = []
while (True):
	retcode = p.poll()
	if not retcode:
		line = p.stdout.readline()
		if line:
			lines.append(line.rstrip())
			if line.startswith('INFO: Hudson is ready.'):
				p.terminate()
				break
	else:
		break
p.wait()

failed = False

for line in lines:
	match = re.match(refailed, line)
	if match:
		plug = match.group(1)
		print 'FAILED:', plug
		failed = True

if failed:
	print "--------------------------log follows-----------------------------"
	for line in lines:
		print line.rstrip()
	print "------------------------------------------------------------------"
	print pluginname, version, "load failed"
else:
	print pluginname, version, 'load succeeded'

