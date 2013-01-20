#!/usr/bin/python
# Provided under The MIT License [http://opensource.org/licenses/MIT]
# Script to change jenkins parent to hudson to test whether
# plugin would load successfully in hudson
# Also makes some changes necessary for an "official" fork
# which are transparent to a build.

# read pom.xml and back it up

import errno, sys, os, string, re
import xml.etree.ElementTree as ET
from json_files import *
from build_replacement_map import build_replacement_map

# Change jenkins parent to hudson

def findOrCreate(parent, tag):
	child = parent.find(tag)
	if child is None:
		child = ET.SubElement(parent, tag)
	return child

def addChild(parent, tag):
	return ET.SubElement(parent, tag)

# http://effbot.org/zone/element-lib.htm#prettyprint
def _indent(elem, level=0):
	i = "\n" + level*"  "
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			_indent(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i

#
# fixpom function
#
# The dir argument is the directory containing the pom.xml file to be fixed
#

def fixpom(dir):
	path = os.path.join(os.path.dirname(__file__), 'replacements.json')
	if not os.path.exists(path):
		build_replacement_map(path)
	replmap = loadFromJson(path)
	
	ns = 'http://maven.apache.org/POM/4.0.0'
	nsc = '{'+ns+'}'
	doc = ET.parse(dir+"/pom.xml")
	doc.write(dir+'/pom.xml.bak', encoding='UTF-8', default_namespace=ns)
	root = doc.getroot()

	parent = root.find(nsc+'parent')
	if parent is None:
		sys.stderr.write('pom.xml has no <parent> element\n')
		return 'No parent'
	artifact = root.find(nsc+'artifactId')
	if artifact is None:
		sys.stderr.write('pom.xml has no <artifactId> element\n')
		return 'No artifactId'
	name = root.find(nsc+'name')
	if name is None:
		name = ET.SubElement(root, nsc+'name')
		name.text = artifact.text

	"""
    	<parent>
        	<groupId>org.eclipse.hudson.plugins</groupId>
        	<artifactId>hudson-plugin-parent</artifactId>
        	<version>3.0.0</version>
    	</parent>
	"""
	group = findOrCreate(parent, nsc+'groupId')
	if group.text == None:
		sys.stderr.write('Plugin has no <parent><groupId>')
		return 'No parent groupId'
	match = re.search(r"jenkins|org\.jvnet\.hudson", group.text)
	if not match:
		sys.stderr.write("<parent><groupId>"+group.text+" unexpected value")
		return 'Parent groupId '+group.text
	group.text = 'org.eclipse.hudson.plugins'
	parentArtifact = findOrCreate(parent, nsc+'artifactId')
	parentArtifact.text = 'hudson-plugin-parent'
	version = findOrCreate(parent, nsc+'version')
	version.text = '3.0.0'

	# jenkins plugins frequently have no groupId
	# in any case, change it to org.hudsonci.plugins

	groupId = findOrCreate(root, nsc+'groupId')
	groupId.text = 'org.hudsonci.plugins'
	
	# assume result will be a fork, so fix version
	
	version = root.find(nsc+'version')
	if version is None:
		return "plugin has no version"
	match = re.match(r"(.*)(-SNAPSHOT)?", version.text)
	if not match:
		return "Can't parse plugin version"
	version.text = match.group(1)+"-h-1-SNAPSHOT"

	# remove jenkins repository so plugins loaded from jenkins
	# won't be available

	repo = root.find(nsc+'repositories')
	if repo is not None:
		for r in repo.findall(nsc+'repository'):
			id = r.find(nsc+'id')
			if id is not None and 'jenkins' in id.text:
				r.remove()

	pluginRepo = root.find(nsc+'pluginRepositories')
	if pluginRepo is not None:
		root.remove(pluginRepo)
	
	# replace Jenkins in name with Hudson

	if name.text is not None:
		text = name.text.strip()
		repl = 'jenkins'
		pos = text.find(repl)
		if pos < 0:
			repl = 'Jenkins'
			pos = text.find(repl)
		if pos >= 0:
			name.text = text.replace(repl, 'Hudson')
			
	# fix documentation URL

	url = root.find(nsc+'url')
	if url is not None:
		urltext = url.text.replace('jenkins-ci', 'hudson-ci')
		urltext = urltext.replace('JENKINS', 'HUDSON')
		url.text = urltext
	else:
		url = ET.SubElement(root, nsc+'url')
		escname = name.text.replace(' ', '+')
		url.text = 'http://wiki.hudson-ci.org/display/HUDSON/' + escname

	# fix scm

	"""
  	<scm>
    	<connection>scm:git:git://github.com/hudson3-plugins/console-column-plugin.git</connection>
    	<developerConnection>scm:git:git@github.com:hudson3-plugins/console-column-plugin.git</developerConnection>
    	<url>https://github.com/hudson3-plugins/console-column-plugin</url>
  	</scm>
	"""
	scm = findOrCreate(root, nsc+'scm')
	artifactId = artifact.text
	connection = findOrCreate(scm, nsc+'connection')
	connection.text = 'scm:git:git://github.com/hudson3-plugins/' + artifactId + '.git'
	devConnection = findOrCreate(scm, nsc+'developerConnection')
	devConnection.text = 'scm:git:git@github.com:hudson3-plugins/' + artifactId + '.git'
	scmUrl = findOrCreate(scm, nsc+'url')
	scmUrl.text = 'https://github.com/hudson3-plugins/' + artifactId

	# get rid of distributionManagement

	distm = root.find(nsc+'distributionManagement')
	if distm is not None:
		root.remove(distm)

	# if no license, make it MIT

	"""
  	<licenses>
    	<license>
      	<name>The MIT license</name>
      	<url>http://opensource.org/licenses/MIT</url>
      	<distribution>repo</distribution>
    	</license>
  	</licenses>
	"""
	licenses = root.find(nsc+'licenses')
	if licenses is None:
		licenses = addChild(root, nsc+'licenses')
		license = addChild(licenses, nsc+'license')
		licenseName = addChild(license, nsc+'name')
		licenseName.text = 'The MIT license'
		licenseUrl = addChild(license, nsc+'url')
		licenseUrl.text = 'http://opensource.org/licenses/MIT'
		licenseDistro = addChild(license, nsc+'distribution')
		licenseDistro.text = 'repo'

	# if no developers, add self as developer with role maintainer

	"""
  	<developers>
    	<developer>
      	<id>bobfoster</id>
      	<name>Bob Foster</name>
      	<email>bobfoster@gmail.com</email>
      	<role>Maintainer</role>
    	</developer>
  	</developers>
	"""
	developers = root.find(nsc+'developers')
	if developers is None:
		developers = addChild(root, nsc+'developers')
		developer = addChild(developers, nsc+'developer')
		devId = addChild(developer, nsc+'id')
		devId.text = 'bobfoster'
		devName = addChild(developer, nsc+'name')
		devName.text = 'Bob Foster'
		devEmail = addChild(developer, nsc+'email')
		devEmail.text = 'bobfoster@gmail.com'
		devRoles = addChild(developer, nsc+'roles')
		devRole = addChild(devRoles, nsc+'role')
		devRole.text = 'Hudson Maintainer'

	# if no properties, or no hudsonTags property, add a single tag
	# this will probably need to be manually corrected

	props = findOrCreate(root, nsc+'properties')
	hudsonTags = props.find(nsc+'hudsonTags')
	if hudsonTags is None:
		hudsonTags = addChild(props, nsc+'hudsonTags')
		hudsonTags.text = 'misc'

	# Sonatype requires <description>
	# If none, make it same as name

	description = root.find(nsc+'description')
	if description is None:
		description = addChild(root, nsc+'description')
		description.text = name.text

	# Go through dependencies, replacing with Hudson equivalents
	
	deps = root.find(nsc+'dependencies')
	if deps is not None:
		for dep in deps.findall(nsc+'dependency'):
			departifact = dep.find(nsc+'artifactId')
			artifactId = departifact.text
			repl = replmap.get(artifactId, None)
			if repl:
				artifactId = repl['artifactId']
				depgroup = findOrCreate(dep, nsc+'groupId')
				depgroup.text = repl['groupId']
				depversion = findOrCreate(dep, nsc+'version')
				depversion.text = repl['version']
				
	# todo move groupId to before artifactId
	# todo blank lines separate element groups

	_indent(root)

	doc.write(dir+'/pom.xml', encoding='UTF-8', default_namespace=ns)
	
	return 'Fixed'

# Run as standalone program

if __name__ == '__main__':
	dir = '.'
	if len(sys.argv) == 2:
		dir = sys.argv[1]
	fixpom(dir)





