#!/usr/bin/python
#

import re

versionre = re.compile(r"\d+")

def cmpversion(v1, v2):
	v1match = re.findall(versionre, v1)
	v2match = re.findall(versionre, v2)
	v1cmp = map(int, v1match)
	v2cmp = map(int, v2match)
	return cmp(v1cmp, v2cmp)
