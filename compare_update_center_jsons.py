#!/usr/bin/python
#
# Compare two files in update center format - which is not quite JSON -
# to make sure they have the same plugins in the same version.
#
# Self-contained script.

import urllib, json, sys, os

if len(sys.argv) != 3:
	print "Usage: ./compare_update_center_jsons.py OLD_UC_URL NEW_UC_URL"
	print "       Hint: Use file:/// URL for the NEW_UC_URL"
	sys.exit(1)

def read_update_center(url):
	file = urllib.urlopen(url)
	text = file.read()
	file.close()
	if text.startswith('updateCenter.post(') and text.endswith(');'):
		js = text[len('updateCenter.post('): -2].strip()
		return json.loads(js)
	else:
		return {'plugins': None}

def sanity_check(plugins, what):
	if plugins is None:
		print "No plugins in %s" % what
		sys.exit(1)

old_uc = read_update_center(sys.argv[1])
new_uc = read_update_center(sys.argv[2])

old_plugins = old_uc['plugins']
new_plugins = new_uc['plugins']

sanity_check(old_plugins, "OLD_UC_URL")
sanity_check(new_plugins, "NEW_UC_URL")

print str(len(old_plugins)), "in OLD_UC_URL"
print str(len(new_plugins)), "in NEW_UC_URL"

different = len(old_plugins) != len(new_plugins)

for key, value in old_plugins.items():
	newvalue = new_plugins.get(key, None)
	if not newvalue:
		print "Old plugin %s not in new plugins" % key
		different = True
	else:
		if value['version'] != newvalue['version']:
			print "Plugin %s old version %s new version %s" % (key, value['version'], newvalue['version'])
			different = True

for key, value in new_plugins.items():
	oldvalue = old_plugins.get(key, None)
	if not oldvalue:
		print "New plugin %s not in old plugins" % key
		different = True

if different:
	print "Old and new plugins are NOT the same"
else:
	print "Old and new plugins match"



