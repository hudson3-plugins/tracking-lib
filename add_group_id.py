#!/usr/bin/python
#
# Add groupId to the plugin entries in update center
#

import urllib, json, sys, os
from read_update_center import *
from json_files import *
from build_replacement_map import *

slow = False
out = 'update-center.json'

if len(sys.argv) > 1:
	if sys.argv[1] == '-slow':
		slow = True
		if len(sys_argv) == 3:
			out = sys.argv[2]
	else:
		out = sys.argv[1]
		
repl = get_replacement_map_slow() if slow else get_replacement_map()

uc = read_hudson3_update_center()
plugins = uc['plugins']

remove = []
add = {}
depdeleted = []

for key, value in plugins.items():
	r = repl.get(key, None)
	if not r:
		print '%s is not in the replacement map!' % key
	else:
		value['groupId'] = r['groupId']
		name = r['artifactId']
		if key != name:
			remove.append(key)
			add[name] = value
		deps = value['dependencies']
		for i in range(len(deps) -1, -1, -1):
			dep = deps[i]
			if not dep['name'] or dep['name'] == 'null':
				del deps[i]
				depdeleted.append(key)

for key in remove:
	del plugins[key]
	print 'Deleted %s' % key
for key, value in add.items():
	plugins[key] = value
	print 'Added %s' % key

print str(len(depdeleted)), "null dependencies deleted"
if len(depdeleted) > 0:
	print 'See deleted_dep.json'

dumpAsJson("deleted_dep.json", depdeleted)

write_update_center(out, uc)


