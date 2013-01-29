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

def _replace_plugin(parent, artifactId):
	global _replmap
	global _nsc
	repl = _replmap.get(artifactId, None)
	if repl is not None:
		artifact = _findOrCreate(parent, _nsc+'artifactId')
		artifact.text = repl['artifactId']
		group = _findOrCreate(parent, _nsc+'groupId')
		group.text = repl['groupId']
		versionRange = parent.find(_nsc+'versionRange')
		if versionRange is not None:
			versionRange.text = '['+repl['version']+',)'
		else:
			version = _findOrCreate(parent, _nsc+'version')
			version.text = repl['version']
		return True
	return False

def _get_parent(child, ancestor):
	for c in ancestor.getchildren():
		if c == child:
			return ancestor
		parent = _get_parent(child, c)
		if parent is not None:
			return parent
	return None

def _fix_artifacts(element):
	global _nsc
	for art in element.findall('.//'+_nsc+'artifactId'):
		artifactId = art.text
		parent = _get_parent(art, element)
		_replace_plugin(parent, artifactId) 

#
# fixpom function
#
# The dir argument is the directory containing the pom.xml file to be fixed
#

def fixpom(dir):
	path = os.path.join(os.path.dirname(__file__), 'replacements.json')
	if not os.path.exists(path):
		build_replacement_map(path)
	global _replmap
	_replmap = loadFromJson(path)
	
	requireFork = False
	
	ns = 'http://maven.apache.org/POM/4.0.0'
	global _nsc
	_nsc = '{'+ns+'}'
	bakpath = dir+'/pom.xml.bak'
	pompath = dir+"/pom.xml"
	if os.path.exists(bakpath):
		os.remove(bakpath)
	doc = ET.parse(pompath)
	doc.write(bakpath, encoding='UTF-8', default_namespace=ns)
	root = doc.getroot()

	#-----------------------------------------------------------
	# Error check plugin and parent

	parent = root.find(_nsc+'parent')
	if parent is None:
		sys.stderr.write('pom.xml has no <parent> element\n')
		return 'No parent'
	artifact = root.find(_nsc+'artifactId')
	if artifact is None:
		sys.stderr.write('pom.xml has no <artifactId> element\n')
		return 'No artifactId'
	name = root.find(_nsc+'name')
	if name is None:
		name = ET.SubElement(root, _nsc+'name')
		name.text = artifact.text
	parentgroup = _findOrCreate(parent, _nsc+'groupId')
	if parentgroup.text is None or parentgroup.text == '':
		sys.stderr.write('Plugin has no <parent><groupId>')
		return 'No parent groupId'
	parentversion = _findOrCreate(parent, _nsc+'version')
	if parentversion.text is None or parentversion.text == '':
		sys.stderr.write('Plugin has no <parent><version>')
		return 'No parent version'
	parentartifact = _findOrCreate(parent, _nsc+'artifactId')
	if parentartifact.text is None or parentartifact.text == '':
		sys.stderr.write('Plugin has no <parent><artifactId>')
		return 'No parent artifactId'
	
	#-----------------------------------------------------------
	# Fix parent
	
	"""
    	<parent>
        	<groupId>org.eclipse.hudson.plugins</groupId>
        	<artifactId>hudson-plugin-parent</artifactId>
        	<version>3.0.0</version>
    	</parent>
	"""
	# relativePath is often wrong - disable it
	relativePath = _findOrCreate(parent, _nsc+'relativePath')
	relativePath.text = ''
	
	repl = _replmap.get(parentartifact.text, None)
	if repl:
		parentartifact.text = repl['artifactId']
		parentgroup.text = repl['groupId']
		parentversion.text = repl['version']
		requireFork = True
	else:
		# Assume some kind of plugin parent
		match = re.search(r"jenkins|org\.jvnet\.hudson", parentgroup.text)
		if not match:
			sys.stderr.write("<parent><groupId>"+parentgroup.text+" unexpected value")
			return 'Parent groupId '+parentgroup.text
		parentgroup.text = 'org.eclipse.hudson.plugins'
		parentartifact.text = 'hudson-plugin-parent'
		parentversion.text = '3.0.0'

	#-----------------------------------------------------------
	# jenkins plugins frequently have no groupId
	# in any case, change it to org.hudsonci.plugins

	groupId = _findOrCreate(root, _nsc+'groupId')
	groupId.text = 'org.hudsonci.plugins'
	
	#-----------------------------------------------------------
	# fix version for a fork (doesn't mean it has to be)
	
	version = root.find(_nsc+'version')
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

	url = root.find(_nsc+'url')
	if url is not None:
		urltext = url.text.replace('jenkins-ci', 'hudson-ci')
		urltext = urltext.replace('JENKINS', 'HUDSON')
		url.text = urltext
	else:
		url = ET.SubElement(root, _nsc+'url')
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
	scm = _findOrCreate(root, _nsc+'scm')
	artifactId = artifact.text
	connection = _findOrCreate(scm, _nsc+'connection')
	connection.text = 'scm:git:git://github.com/hudson3-plugins/' + artifactId + '.git'
	devConnection = _findOrCreate(scm, _nsc+'developerConnection')
	devConnection.text = 'scm:git:git@github.com:hudson3-plugins/' + artifactId + '.git'
	scmUrl = _findOrCreate(scm, _nsc+'url')
	scmUrl.text = 'https://github.com/hudson3-plugins/' + artifactId

	#-----------------------------------------------------------
	# get rid of distributionManagement

	distm = root.find(_nsc+'distributionManagement')
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
	licenses = root.find(_nsc+'licenses')
	if licenses is None:
		licenses = _addChild(root, _nsc+'licenses')
		license = _addChild(licenses, _nsc+'license')
		licenseName = _addChild(license, _nsc+'name')
		licenseName.text = 'The MIT license'
		licenseUrl = _addChild(license, _nsc+'url')
		licenseUrl.text = 'http://opensource.org/licenses/MIT'
		licenseDistro = _addChild(license, _nsc+'distribution')
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
	developers = root.find(_nsc+'developers')
	if developers is None:
		developers = _addChild(root, _nsc+'developers')
		developer = _addChild(developers, _nsc+'developer')
		devId = _addChild(developer, _nsc+'id')
		devId.text = 'bobfoster'
		devName = _addChild(developer, _nsc+'name')
		devName.text = 'Bob Foster'
		devEmail = _addChild(developer, _nsc+'email')
		devEmail.text = 'bobfoster@gmail.com'
		devRoles = _addChild(developer, _nsc+'roles')
		devRole = _addChild(devRoles, _nsc+'role')
		devRole.text = 'Hudson Maintainer'

	#-----------------------------------------------------------
	# if no properties, or no hudsonTags property, add a single tag
	# this will probably need to be manually corrected

	props = _findOrCreate(root, _nsc+'properties')
	hudsonTags = props.find(_nsc+'hudsonTags')
	if hudsonTags is None:
		hudsonTags = _addChild(props, _nsc+'hudsonTags')
		hudsonTags.text = 'misc'

	#-----------------------------------------------------------
	# Sonatype requires <description>
	# If none, make it same as name

	description = root.find(_nsc+'description')
	if description is None:
		description = _addChild(root, _nsc+'description')
		description.text = name.text

	#-----------------------------------------------------------
	# Go through dependencies, replacing with Hudson equivalents
	#
	# Prior to dependency replacement, we haven't done anything
	# that would require a fork. However, if a plugin has been
	# forked, the original won't work in Hudson.

	requireFork = False
	depgroups = []
	deps = root.find(_nsc+'dependencies')
	for art in deps.findall('.//'+_nsc+'artifactId'):
		artifactId = art.text
		dep = _get_parent(art, deps)
		if _replace_plugin(dep, artifactId):
			depgroup = dep.find(_nsc+'groupId')
			if depgroup is not None:
				depgroups.append(depgroup.text)
			#------------------------------------------------------
			# If a dependency is a fork, this plugin must be forked
			#
			depversion = dep.find(_nsc+'version')
			if depversion is not None:
				version = depversion.text
				requireFork = requireFork or '-h-' in version or '-hudson-' in version
	
	#-----------------------------------------------------------
	# Do the same with plugins, replacing with Hudson equivalents
	#
	build = root.find(_nsc+'build')
	if build is not None:
		_fix_artifacts(build)
	
	#-----------------------------------------------------------
	# After this, some Jenkins plugins may remain.
	# If not, remove jenkins repository.

	if len([x for x in depgroups if 'jenkins' in x]) == 0:
		repo = root.find(_nsc+'repositories')
		if repo is not None:
			for r in repo.findall(_nsc+'repository'):
				id = r.find(_nsc+'id')
				if id is not None and 'jenkins' in id.text:
					repo.remove(r)

		pluginRepo = root.find(_nsc+'pluginRepositories')
		if pluginRepo is not None:
			root.remove(pluginRepo)
	
	#-----------------------------------------------------------
	# Certain plugins will require source changes and/or the
	# source implies an added dependency.
	
	fixes = fixsource()
	for key, value in fixes.items():
		if value['sourceChange']:
			requireFork = True
		dependency = value['dependency']
		if dependency:
			requireFork = True
			if deps is None:
				deps = _addChild(root, _nsc+'dependencies')
			dep = _addChild(deps, _nsc+'dependency')
			_addChild(dep, _nsc+'groupId').text = dependency['groupId']
			_addChild(dep, _nsc+'artifactId').text = dependency['artifactId']
			_addChild(dep, _nsc+'version').text = dependency['version']

	#-----------------------------------------------------------
	# todo move groupId to before artifactId
	# todo blank lines separate element groups

	_indent(root)

	doc.write(pompath, encoding='UTF-8', default_namespace=ns)
	
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
	print fixpom(dir)





