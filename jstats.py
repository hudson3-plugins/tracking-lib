#!/usr/bin/python
import sys, re, os, json, urllib
#
# Use jenkins plugin installation trend data to derive plugin popularity ranking
#

def dumpAsJson(filename, array):
	dump = json.dumps(array, sort_keys = True, indent = 4)
	f = open(filename, 'w')
	f.write(dump)
	f.close()

def gethighkey(dict):
	high = ""
	for key, value in dict.items():
		if key > high:
			high = key
	return high, dict[high]

#------------------------------------------------
# Open trend folder as HTML page and scrape it
# for individual plugin JSON links

statpage = "http://stats.jenkins-ci.org/plugin-installation-trend/"

sock = urllib.urlopen(statpage) 
htmlSource = sock.read()                            
sock.close()

anchors = re.findall(r'<a\s*href="([^"]*)', htmlSource)

numanchors = len(anchors)
print str(numanchors), "anchors"

"""
print "First 10:"
for i in range(0, 10):
	print anchors[i]
print "Last 10:"
for i in range(numanchors-10, numanchors):
	print anchors[i]
"""

#------------------------------------------------
# Stats are the combined latest measurements for each plugin

pstats = {}

for i in range(0, numanchors):
	anchor = anchors[i]
	if anchor.startswith('?') or anchor.startswith('/'):
		continue
	
	# print heartbeat - this takes awhile
	sys.stdout.write('.')
	sys.stdout.flush()
	
	sock = urllib.urlopen(statpage+anchor) 
	plug = json.load(sock)                        
	sock.close()
	if plug.get("name", False):
		name = plug["name"]
		installTS, install = gethighkey(plug["installations"])
		percentTS, percent = gethighkey(plug["installationsPercentage"])
		pstats[name] = obj = {}
		obj["install"] = install
		obj["percent"] = percent
		obj["installTS"] = installTS
		obj["percentTS"] = percentTS
		
	"""
	else:
		print "----------------"
		print json.dumps(plug)
		print "----------------"
	"""
print

#------------------------------------------------
# Save JSON results and print summary.
# NB: The data need further cleaning. See top.py.

dumpAsJson("jenkinsstats.json", pstats)

print str(len(pstats)), "plugins (jenkinsstats.json)"
