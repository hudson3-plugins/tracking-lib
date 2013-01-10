#!/usr/bin/python
#

import re

_versionre = re.compile(r"\d+")

def cmpversion(v1, v2):
	v1match = re.findall(_versionre, v1)
	v2match = re.findall(_versionre, v2)
	v1cmp = map(int, v1match)
	v2cmp = map(int, v2match)
	return cmp(v1cmp, v2cmp)

def testcmpversion():
	print __debug__
	assert cmpversion('None', '0') < 0, "Fail"
	assert cmpversion('None', 'None') == 0, "Fail"
	assert cmpversion('0', 'None') > 0, "Fail"
	assert cmpversion('1.2-h-1', '1.2') > 0, "Fail"
	assert cmpversion('1.100', '1.2') > 0, "Fail"
	assert cmpversion('1.1', '1.1.1') < 0, "Fail"
	