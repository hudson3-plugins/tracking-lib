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
	input = opener.open(url)
	output = open(path, 'wb')
	try:
		output.write(input.read())
	finally:
		output.close()
		input.close()

if __name__ == "__main__":
	if len(sys.argv) != 3:
		print "Usage: ./urlretrieve URL FILE_PATH"
		sys.exit(1)
	print sys.argv[1], sys.argv[2]
	urlretrieve(sys.argv[1], sys.argv[2])

		