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
