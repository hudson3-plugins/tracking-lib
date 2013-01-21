#!/usr/bin/python
#

import urllib, json, sys, os

def _fix_proxy(protocol):
	proxy = os.environ.get(protocol+'_proxy', None)
	if proxy:
		if not proxy.startswith("http:") and not proxy.startswith("https:"):
			proxy = protocol+"://"+proxy
	return proxy

def _add_proxy(protocol, proxymap):
	proxy = _fix_proxy(protocol)
	if proxy:
		proxymap[protocol] = proxy

def get_proxy_map():
	proxymap = {}
	_add_proxy('http', proxymap)
	_add_proxy('https', proxymap)
	return proxymap

def read_update_center(url):
	file = urllib.urlopen(url, None, get_proxy_map())
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
