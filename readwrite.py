#!/usr/bin/python
#

import subprocess, os, sys, re
from json_files import *

contents = None
try:
	with open('localfile', 'r') as f:
		print 'localfile exists'
		contents = f.read()
		f.close()
except IOError as e:
	print 'localfile does not exist'

if contents:
	print 'localfile contents: '+contents

f = open('localfile', 'w')
print >>f, 'Now is the time for all good men'
f.close()