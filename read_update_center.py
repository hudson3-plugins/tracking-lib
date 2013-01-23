#!/usr/bin/python
#

import urllib, json, sys, os
from json_files import dumpAsJson

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

def read_hudson3_update_center():
	return read_update_center("http://hudson-ci.org/update-center3/update-center.json")

def read_hudson3_plugins():
	return read_plugins("http://hudson-ci.org/update-center3/update-center.json")

def write_update_center(path, data):
	f = open(path, 'w')
	f.write('updateCenter.post(%s);' % json.dumps(data))
	f.close()

if __name__ == '__main__':
	nargs = len(sys.argv)
	if nargs < 2 or nargs > 3:
		print 'Usage: ./read_update_center TO_PATH [URL]'
		sys.exit(1)
	url = "http://hudson-ci.org/update-center3/update-center.json"
	if nargs == 3:
		url = sys.argv[2]
	uc = read_update_center(url)
	dumpAsJson(sys.argv[1], uc)
