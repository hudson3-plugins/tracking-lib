#!/usr/bin/python
import subprocess, errno, sys, re, os
import urllib, shutil
from json_files import *
from read_update_center import *

if len(sys.argv) != 2:
	print 'Usage: ./load_test_hudson.py HUDSON_WAR_PATH'

def cmd(args):
	if subprocess.call(args):
		print 'FAILED: '+' '.join(args)
		sys.exit(1)

def cmds(str):
	cmd(str.split(' '))

def read_plugins(url, who):
	plugins = read_update_center(url)['plugins']
	if not plugins:
		print "Can't read", who, "update center"
		sys.exit(1)
	return plugins
	
def freshdir(path):
	if os.path.exists(path):
		shutil.rmtree(path, True)
	cmd(['mkdir', path])

hplugins = read_plugins("http://hudson-ci.org/update-center3/update-center.json", 'hudson')

print str(len(hplugins)), 'plugins in hudson3 update center'

#if not os.path.exists('hudson.war'):
#	urllib.urlretrieve("http://www.eclipse.org/downloads/download.php?file=/hudson/war/hudson-3.0.0.war",
#						"hudson.war")

#freshdir('plugins')

rename = re.compile('/([-_a-zA-Z0-9]*\.hpi)')

#
# Load plugin hpi files and build collect direct dependencies
#

print "Loading plugin hpi files"

work = {}
for key, value in hplugins.items():
	url = value['url']
	match = re.search(rename, url)
	if not match:
		print "Can't find name in ", pluginurl
		continue
	#urllib.urlretrieve(url, 'plugins/'+match.group(1))
	deps = value['dependencies']
	depends = set()
	for dep in deps:
		depname = dep.get('name', None)
		# null in json file seems to be translated to 'null'
		if depname and not depname == 'null':
			depends.add(depname)
	work[key] = {'hpiname': match.group(1), 'depends': depends}

#
# Collect recursive dependencies for all plugins
#

print "Calculate recursive dependencies"

def finddeps(plugin, depends, allset):
	for dep in depends:
		if dep not in allset:
			allset.add(dep)
			value = work.get(dep, None)
			if not value:
				print "Can't find dependency", dep, "for plugin", plugin
				continue
			finddeps(dep, value['depends'], allset)

for key, value in work.items():
	allset = set()
	finddeps(key, value['depends'], allset)
	value['depends'] = allset

#
# Load test each plugin with its dependencies in otherwise empty hudson_home
#

print "Load plugins in Hudson"

home = {'HUDSON_HOME': './hudson_home'}
run = ['java', '-jar', sys.argv[1], '--httpPort=18080', '--skipInitSetup']
refailed = re.compile(r"SEVERE: Failed Loading plugin ([-_a-zA-Z0-9]*)")
failed = {}

def loadtest(plugin):
	freshdir('hudson_home')
	cmds('mkdir hudson_home/plugins')
	
	value = work[plugin]
	hpiname = value['hpiname']
	cmd(['cp', 'plugins/'+hpiname, 'hudson_home/plugins/'])
	deps = value['depends']
	for dep in deps:
		hpidep = work[dep]['hpiname']
		cmd(['cp', 'plugins/'+hpidep, 'hudson_home/plugins/'])
		
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
	
	for line in lines:
		match = re.match(refailed, line)
		if match:
			plug = match.group(1)
			failed[plug] = {'log': lines, 'depends': deps}
			print 'FAILED: '+plug

num = 0
for key, value in hplugins.items():
	loadtest(key)
	num += 1
	if num % 10 == 0:
		print num, 'tested'

dumpAsJson('load_fail.json', failed)

print str(len(failed)), "hudson plugins failed to load"
if len(failed) > 0:
	print 'See load_fail.json for failure logs'

