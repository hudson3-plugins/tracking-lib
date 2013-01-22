#!/usr/bin/python
#
# Add groupId to the plugin entries in update center
#

import urllib, json, sys, os
from read_update_center import *
from json_files import *
from build_replacement_map import *

repl = get_replacement_map()
uc = read_hudson3_update_center()
plugins = uc['plugins']

for key, value in plugins.items():
	r = repl.get(key, None)
	if not r:
		print '%s is not in the replacement map!' % key
	else:
		value['groupId'] = r['groupId']

write_update_center('./update-center.json', uc)


