#!/usr/bin/python
#

import urllib, json, sys

def read_update_center(url):
	file = urllib.urlopen(url)
	text = file.read()
	file.close()
	if text.startswith('updateCenter.post(') and text.endswith(');'):
		js = text[len('updateCenter.post('): -2].strip()
		return json.loads(js)
	else:
		return {'plugins': None}
