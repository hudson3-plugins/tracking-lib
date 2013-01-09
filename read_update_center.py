#!/usr/bin/python
#

import urllib, json, sys
from json_files import *

if len(sys.argv) != 3:
	print "Usage: ./read_update_center.py URL OUTPUT_FILE"
	sys.exit(1)

file = urllib.urlopen(sys.argv[1])
text = file.read()
file.close()
if text.startswith('updateCenter.post(') and text.endswith(');'):
	js = text[len('updateCenter.post('): -2].strip()
	state = json.loads(js)
	dumpAsJson(sys.argv[2], state)
	plugins = state['plugins']
	print str(len(plugins))+' plugins in '+sys.argv[2]
else:
	sys.exit(1)
