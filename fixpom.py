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
from fixsource import fixsource

# Change jenkins parent to hudson

def _findOrCreate(parent, tag):
	child = parent.find(tag)
	if child is None:
		child = ET.SubElement(parent, tag)
	return child

def _addChild(parent, tag):
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
	group = _findOrCreate(parent, nsc+'groupId')
	if group.text == None:
		sys.stderr.write('Plugin has no <parent><groupId>')
		return 'No parent groupId'
	match = re.search(r"jenkins|org\.jvnet\.hudson", group.text)
	if not match:
		sys.stderr.write("<parent><groupId>"+group.text+" unexpected value")
		return 'Parent groupId '+group.text
	group.text = 'org.eclipse.hudson.plugins'
	parentArtifact = _findOrCreate(parent, nsc+'artifactId')
	parentArtifact.text = 'hudson-plugin-parent'
	version = _findOrCreate(parent, nsc+'version')
	version.text = '3.0.0'

	#-----------------------------------------------------------
	# jenkins plugins frequently have no groupId
	# in any case, change it to org.hudsonci.plugins

	groupId = _findOrCreate(root, nsc+'groupId')
	groupId.text = 'org.hudsonci.plugins'
	
	#-----------------------------------------------------------
	# fix version for a fork (doesn't mean it has to be)
	
	version = root.find(nsc+'version')
	if version is None:
		return "plugin has no version"
	match = re.match(r"(.*)(-SNAPSHOT)?", version.text)
	if not match:
		return "Can't parse plugin version"
	version.text = match.group(1)+"-h-1-SNAPSHOT"

	#-----------------------------------------------------------
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
			
	#-----------------------------------------------------------
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

	#-----------------------------------------------------------
	# fix scm

	"""
  	<scm>
    	<connection>scm:git:git://github.com/hudson3-plugins/console-column-plugin.git</connection>
    	<developerConnection>scm:git:git@github.com:hudson3-plugins/console-column-plugin.git</developerConnection>
    	<url>https://github.com/hudson3-plugins/console-column-plugin</url>
  	</scm>
	"""
	scm = _findOrCreate(root, nsc+'scm')
	artifactId = artifact.text
	connection = _findOrCreate(scm, nsc+'connection')
	connection.text = 'scm:git:git://github.com/hudson3-plugins/' + artifactId + '.git'
	devConnection = _findOrCreate(scm, nsc+'developerConnection')
	devConnection.text = 'scm:git:git@github.com:hudson3-plugins/' + artifactId + '.git'
	scmUrl = _findOrCreate(scm, nsc+'url')
	scmUrl.text = 'https://github.com/hudson3-plugins/' + artifactId

	#-----------------------------------------------------------
	# get rid of distributionManagement

	distm = root.find(nsc+'distributionManagement')
	if distm is not None:
		root.remove(distm)

	#-----------------------------------------------------------
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
		licenses = _addChild(root, nsc+'licenses')
		license = _addChild(licenses, nsc+'license')
		licenseName = _addChild(license, nsc+'name')
		licenseName.text = 'The MIT license'
		licenseUrl = _addChild(license, nsc+'url')
		licenseUrl.text = 'http://opensource.org/licenses/MIT'
		licenseDistro = _addChild(license, nsc+'distribution')
		licenseDistro.text = 'repo'

	#-----------------------------------------------------------
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
		developers = _addChild(root, nsc+'developers')
		developer = _addChild(developers, nsc+'developer')
		devId = _addChild(developer, nsc+'id')
		devId.text = 'bobfoster'
		devName = _addChild(developer, nsc+'name')
		devName.text = 'Bob Foster'
		devEmail = _addChild(developer, nsc+'email')
		devEmail.text = 'bobfoster@gmail.com'
		devRoles = _addChild(developer, nsc+'roles')
		devRole = _addChild(devRoles, nsc+'role')
		devRole.text = 'Hudson Maintainer'

	#-----------------------------------------------------------
	# if no properties, or no hudsonTags property, add a single tag
	# this will probably need to be manually corrected

	props = _findOrCreate(root, nsc+'properties')
	hudsonTags = props.find(nsc+'hudsonTags')
	if hudsonTags is None:
		hudsonTags = _addChild(props, nsc+'hudsonTags')
		hudsonTags.text = 'misc'

	#-----------------------------------------------------------
	# Sonatype requires <description>
	# If none, make it same as name

	description = root.find(nsc+'description')
	if description is None:
		description = _addChild(root, nsc+'description')
		description.text = name.text

	#-----------------------------------------------------------
	# Go through dependencies, replacing with Hudson equivalents
	
	depgroups = []
	deps = root.find(nsc+'dependencies')
	if deps is not None:
		for dep in deps.findall(nsc+'dependency'):
			departifact = dep.find(nsc+'artifactId')
			artifactId = departifact.text
			depgroup = dep.find(nsc+'groupId')
			repl = replmap.get(artifactId, None)
			if repl:
				departifact.text = repl['artifactId']
				depgroup = _findOrCreate(dep, nsc+'groupId')
				depgroup.text = repl['groupId']
				depversion = _findOrCreate(dep, nsc+'version')
				depversion.text = repl['version']
			if depgroup:
				depgroups.append(depgroup.text)
	
	#-----------------------------------------------------------
	# Prior to dependency replacement, we haven't done anything
	# that would require a fork. However, if a plugin has been
	# forked, the original won't work in Hudson.
	
	requireFork = False
	if deps is not None:
		for dep in deps.findall(nsc+'dependency'):
			depversion = dep.find(nsc+'version')
			if depversion and ('-h-' in depversion or '-hudson-' in depversion):
				requireFork = True
				break

	#-----------------------------------------------------------
	# After this, some Jenkins plugins may remain.
	# If not, remove jenkins repository.

	if len([x for x in depgroups if 'jenkins' in x]) == 0:
		repo = root.find(nsc+'repositories')
		if repo is not None:
			for r in repo.findall(nsc+'repository'):
				id = r.find(nsc+'id')
				if id is not None and 'jenkins' in id.text:
					r.remove()

		pluginRepo = root.find(nsc+'pluginRepositories')
		if pluginRepo is not None:
			root.remove(pluginRepo)
	
	#-----------------------------------------------------------
	# Certain plugins will require source changes and/or the
	# source implies an added dependency.
	
	fixes = fixsource()
	for key, value in fixes.items():
		if value['sourceChanged']:
			requireFork = True
		dependency = value['dependency']
		if dependency:
			requireFork = True
			if deps is None:
				deps = _addChild(root, nsc+'dependencies')
			dep = _addChild(deps, nsc+'dependency')
			_addChild(dep, nsc+'groupId').text = dependency['groupId']
			_addChild(dep, nsc+'artifactId').text = dependency['artifactId']
			_addChild(dep, nsc+'version').text = dependency['version']

	#-----------------------------------------------------------
	# todo move groupId to before artifactId
	# todo blank lines separate element groups

	_indent(root)

	doc.write(dir+'/pom.xml', encoding='UTF-8', default_namespace=ns)
	
	if requireFork:
		return 'Forked'
	return 'Fixed'

#
# Run as standalone program
#

if __name__ == '__main__':
	dir = '.'
	if len(sys.argv) == 2:
		dir = sys.argv[1]
	fixpom(dir)





