#!/usr/bin/python
import subprocess, errno, sys, re, os
import urllib, shutil
from json_files import *
from read_update_center import *
from utils import *
import zipfile

if len(sys.argv) != 3:
	print 'Usage: ./load_test_hudson.py HUDSON_WAR_PATH HPI_PATH'

filename = sys.argv[2]

hplugins = read_plugins("http://hudson-ci.org/update-center3/update-center.json")

print str(len(hplugins)), 'plugins in hudson3 update center'

freshdir('plugin')

rename = re.compile('/([-_a-zA-Z0-9]*\.hpi)')

# read hpi as zip
# Plugin-Dependencies: subversion:2.3.6-h-1

partifact = re.compile(r"Short-Name: ([-_.a-zA-Z0-9]*)")
pgroup = re.compile(r"Group-Id: ([-_.a-zA-Z0-9]*)")
pversion = re.compile(r"Plugin-Version: ([-_.a-zA-Z0-9]*)")
pany = re.compile(r"[-a-zA-Z0-9]*: ")
pdepend = re.compile(r"Plugin-Dependencies: (.*)")
pcontinue = re.compile(r"(.*)")
pdepends = re.compile(r"([-_.:a-zA-Z0-9]*)(,[-_.a-zA-Z0-9]*)*")
pplug = re.compile(r"([-_.a-zA-Z0-9]*)")

zip = None
pluginname = ""
group = ""
version = ""
deps = ""
try:
	zip = zipfile.ZipFile(filename, 'r')
except:
	print 'Bad zip file at '+filename
if zip:
	mf = zip.open('META-INF/MANIFEST.MF')
	indeps = False
	for line in mf:
		if indeps:
			match = re.match(pany, line)
			if match:
				indeps = False
			else:
				match = re.match(pcontinue, line)
				deps = deps + match.groups()[0].strip()
				continue
		match = re.match(pdepend, line)
		if match:
			indeps = True
			deps = match.groups()[0].strip()
			continue
		match = re.match(partifact, line)
		if match:
			pluginname = match.groups()[0]
		match = re.match(pgroup, line)
		if match:
			group = match.groups()[0]
		match = re.match(pversion, line)
		if match:
			version = match.groups()[0]
	zip.close()

# get the dependency plugin names only
depends = set()
if len(deps) > 0:
	match = re.match(pdepends, deps)
	if match:
		for gp in match.groups():
			if gp:
				if gp.startswith(","):
					gp = gp[1:]
				match = re.match(pplug, gp)
				if match:
					depends.add(match.groups()[0])

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
all.add(pluginname)
for dep in depends:
	if dep and not dep in all:
		finddeps(dep, all)
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
	if dep == pluginname:
		cmd(['cp', filename, 'hudson_home/plugins/'])
	else:
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

cmds('rm -rf hudson_home')

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

