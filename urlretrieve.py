#!//usr/bin/python

import os, sys, urllib2
from read_update_center import get_proxy_map

#
# Retrieve the contents of a url to a local file
#
# Like urllib's urlretrieve except works with proxies
#

def urlretrieve(url, path):
	proxy_handler = urllib2.ProxyHandler(get_proxy_map())
	opener = urllib2.build_opener(proxy_handler)
	f = opener.open(url)
	with open(path, 'wb') as file:
		file.write(f.read())
		