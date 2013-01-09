#!/usr/bin/python
#

import urllib, json
from json_files import *

file = urllib.urlopen("http://updates.jenkins-ci.org/update-center.json")
text = file.read()
file.close()
if text.startswith('updateCenter.post(') and text.endswith(');'):
	js = text[len('updateCenter.post('): -2].strip()
	state = json.loads(js)
	dumpAsJson('jenkins-updates.json', state)
	plugins = state['plugins']
	print str(len(plugins))+' plugins in jenkins update center'
else:
	sys.exit(1)
