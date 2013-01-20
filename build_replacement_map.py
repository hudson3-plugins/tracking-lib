#!/usr/bin/python
#
# Script to build dependency replacement tables
# Standalone so it can be modified without changing any logic

import subprocess, os, sys, re, urllib, zipfile
from json_files import *
from read_update_center import *

_repl = {}
rpat3 = re.compile(r"([^:]*):([^:]*):(.*)")
rpat4 = re.compile(r"([^:]*):([^:]*):([^:]*):(.*)")

"""
def testmatch(pat, s):
	match = re.match(pat, s)
	if match:
		print match.groups()
	else:
		print 'no match '+s
testmatch(rpat3, 'a:b:c')
testmatch(rpat4, 'a:b:c')
testmatch(rpat4, 'a:b:c:d')
testmatch(rpat3, 'org.hudsonci.plugins:git:2.2.1-h-1')
testmatch(rpat4, 'org.hudsonci.plugins:token-macro:jar:1.6-h-1')
"""

def clearrepl():
	_repl = {}

def addrepl(groupId, artifactId, version, key=None):
	if not key:
		key = artifactId
	r = _repl[key] = {}
	r['groupId'] = groupId
	r['artifactId'] = artifactId
	r['version'] = version

def addr(replac, key=None):
	match = re.match(rpat4, replac)
	if match:
		gps = match.groups()
		addrepl(gps[0], gps[1], gps[3], key)
	else:
		match = re.match(rpat3, replac)
		if match:
			gps = match.groups()
			addrepl(gps[0], gps[1], gps[2], key)
		else:
			print 'ERROR invalid repl "'+replac+'"'

"""
Winston's original list:

org.jenkins-ci.plugins:token-macro:jar:1.5.1  => org.hudsonci.plugins:token-macro:jar:1.6-h-1
 org.jvnet.maven-jellydoc-plugin:maven-jellydoc-plugin:jar:1.5 => org.jvnet.maven-jellydoc-plugin:maven-jellydoc-plugin:jar:1.3.1
org.jenkins-ci.tools:maven-hpi-plugin:jar:1.67 => org.eclipse.hudson.tools:maven-hpi-plugin:3.0.0
 org.jvnet.hudson.plugins:analysis-core:jar:1.48 => org.hudsonci.plugins:analysis-core:1.47-h-1
 org.jenkins-ci.tools:maven-hpi-plugin:jar:1.90 => org.eclipse.hudson.tools:maven-hpi-plugin:3.0.0
 org.jenkins-ci:htmlunit:jar:2.6-jenkins-6 => org.hudsonci.tools:htmlunit:2.6-hudson-3
 org.jenkinsci.plugins:git:jar:1.1.17 => org.hudsonci.plugins:git:2.2.1-h-1
 org.jenkins-ci.tools:maven-hpi-plugin:jar:1.71 => org.eclipse.hudson.tools:maven-hpi-plugin:3.0.0
 org.jenkins-ci.plugins:run-condition:jar:0.10
 org.jvnet.hudson.plugins:instant-messaging:jar:1.22 => org.hudsonci.plugins:instant-messaging:1.22-h-1
 org.kohsuke.stapler:json-lib:jar:2.1-rev7 => org.kohsuke.stapler:json-lib:jar:2.1-rev6
 org.jenkins-ci.main:jenkins-war:war:1.409.2 => org.eclipse.hudson:hudson-war:3.0.0-RC4
 org.jenkins-ci.plugins:token-macro:jar:1.4 => org.hudsonci.plugins:token-macro:jar:1.6-h-1
 org.jenkins-ci.modules:sshd:jar:1.1 => org.jvnet.hudson:sshd:1.0-pre-hudson-1
 org.kohsuke.stapler:stapler:jar:1.172 => org.eclipse.hudson.stapler:stapler-parent:3.0.0
 org.jenkins-ci.plugins:multiple-scms:jar:0.2
org.jenkins-ci.main:ui-samples-plugin:jar:1.409.2 => org.jvnet.hudson.main:ui-samples-plugin:1.395
 org.jenkins-ci.main:maven-plugin:jar:3.0.0-RC4 => org.hudsonci.plugins:maven-plugin:2.2.2
 org.powermock.api:powermock-api-mockito:jar:1.4.5 => org.powermock:powermock-api-mockito:1.5
 org.jenkinsci.plugins:git:jar:1.1.11 => org.hudsonci.plugins:git:2.2.1-h-1
 org.jvnet.hudson.plugins:analysis-test:jar:1.10 => org.hudsonci.plugins:analysis-test:1.9-h-1
 org.jenkins-ci.plugins:github-api:jar:1.28 => org.kohsuke:github-api:1.33
 org.jenkins-ci.main:maven-plugin:jar:1.409.2 => org.hudsonci.plugins:maven-plugin:2.2.2
 com.google.code.guice:guice:jar:2.0.1 => com.google.inject:guice:3.0
 org.jenkins-ci.main:jenkins-test-harness:jar:1.409.2 => org.jvnet.hudson.main:hudson-test-harness:1.395 (or org.eclipse.hudson:hudson-test-framework:3.0.0-RC4)
 org.jenkins-ci.main:jenkins-core:jar:1.409.2 => org.eclipse.hudson:hudson-core:3.0.0-RC4
 org.powermock.modules:powermock-module-junit4:jar:1.4.5 => org.powermock:powermock-module-junit4:1.5
org.jenkins-ci.lib:dry-run-lib:jar:0.1 => 
org.jenkins-ci.lib:xtrigger-lib:jar:0.18 =>
"""

def build_replacement_map(path):
	clearrepl()
	addr('org.hudsonci.plugins:token-macro:jar:1.6-h-1')
	addr('org.jvnet.maven-jellydoc-plugin:maven-jellydoc-plugin:jar:1.3.1')
	addr('org.eclipse.hudson.tools:maven-hpi-plugin:3.0.0')
	addr('org.hudsonci.plugins:analysis-core:1.47-h-1')
	addr('org.eclipse.hudson.tools:maven-hpi-plugin:3.0.0')
	addr('org.hudsonci.tools:htmlunit:2.6-hudson-3')
	addr('org.hudsonci.plugins:git:2.2.1-h-1')
	addr('org.eclipse.hudson.tools:maven-hpi-plugin:3.0.0')
	addr('org.hudsonci.plugins:instant-messaging:1.22-h-1')
	addr('org.kohsuke.stapler:json-lib:jar:2.1-rev6')
	addr('org.eclipse.hudson:hudson-war:3.0.0-RC4', 'jenkins-war')
	addr('org.jvnet.hudson:sshd:1.0-pre-hudson-1')
	addr('org.eclipse.hudson.stapler:stapler-parent:3.0.0', 'stapler')
	addr('org.jvnet.hudson.main:ui-samples-plugin:1.395')
	addr('org.powermock:powermock-api-mockito:1.5')
	addr('org.hudsonci.plugins:analysis-test:1.9-h-1')
	addr('org.kohsuke:github-api:1.33')
	addr('com.google.inject:guice:3.0')
	addr('org.eclipse.hudson:hudson-test-framework:3.0.0-RC4', 'jenkins-test-harness')
	addr('org.eclipse.hudson:hudson-core:3.0.0-RC4', 'jenkins-core')
	addr('org.powermock:powermock-module-junit4:1.5')
	
	# now go through hudson3-updates plugins, download hpi, read MANIFEST_MF
	# and extract groupId, artifactId, and version

	partifact = re.compile(r"Short-Name: ([-_.a-zA-Z0-9]*)")
	pgroup = re.compile(r"Group-Id: ([-_.a-zA-Z0-9]*)")
	pversion = re.compile(r"Plugin-Version: ([-_.a-zA-Z0-9]*)")

	hudsonplugins = read_hudson3_plugins()
	for key, value in hudsonplugins.items():
		hpiurl = value.get('url', None)
		if hpiurl:
			filename, headers = urllib.urlretrieve(hpiurl)
			artifact = ""
			group = ""
			version = ""
			zip = None
			try:
				zip = zipfile.ZipFile(filename, 'r')
			except:
				print 'Bad zip file for '+key+' at '+hpiurl
			if zip:
				mf = zip.open('META-INF/MANIFEST.MF')
				for line in mf:
					match = re.match(partifact, line)
					if match:
						artifact = match.groups()[0]
					match = re.match(pgroup, line)
					if match:
						group = match.groups()[0]
					match = re.match(pversion, line)
					if match:
						version = match.groups()[0]
				zip.close()
				if len(artifact) > 0 and len(group) > 0 and len(version) > 0:
					addrepl(group, artifact, version)
			os.remove(filename)

	# Save to replacements.json

	dumpAsJson(path, _repl)

if __name__ == '__main__':
	build_replacement_map('./replacements.json')
