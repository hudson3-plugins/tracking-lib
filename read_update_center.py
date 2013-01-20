#!/usr/bin/python
#

import urllib, json, sys, os

def read_update_center(url):
	proxymap = {}
	proxy = os.environ.get('http_proxy', None)
	if proxy:
		if not proxy.startswith("http:") and not proxy.startswith("https:"):
			proxy = "http://"+proxy
		proxymap['http'] = proxy
	file = urllib.urlopen(url, None, proxymap)
	text = file.read()
	file.close()
	if text.startswith('updateCenter.post(') and text.endswith(');'):
		js = text[len('updateCenter.post('): -2].strip()
		return json.loads(js)
	else:
		return {'plugins': None}

def read_plugins(url):
	plugins = read_update_center(url)['plugins']
	if not plugins:
		print "Can't read update center", url
		sys.exit(1)
	return plugins

def read_hudson3_plugins():
	return read_plugins("http://hudson-ci.org/update-center3/update-center.json")
