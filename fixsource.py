#!/usr/bin/python
# Provided under The MIT License [http://opensource.org/licenses/MIT]
# Script to search and/or change Jenkins plugin source and
# detect dependencies.

import errno, sys, os, string, re
from json_files import *
import subprocess

# Roughly organized by most likely to appear

_data = {
  "jfreechart": {
    "dependency": {
      "groupId": "org.hudsonci.plugins",
      "artifactId": "jfreechart-plugin",
      "version": "1.4"
    },
    "files": ["*.java"],
    "detect": [
      r"org\.jfree\.",
      r"hudson\.util\.ColorPalette",
      r"hudson\.util\.Graph",
      r"hudson\.graph\.jfreechart",
      r"hudson\.util\.ChartUtil",
      r"hudson\.util\.DataSetBuilder",
      r"hudson\.util\.NoOverlapCategoryAxis",
      r"hudson\.util\.ShiftedCategoryAxis",
      r"hudson\.util\.StackedAreaRenderer2"
    ],
    "replace": None,
    "sourceChange": False
  },
  "springsecurity": {
  	"dependency": None,
  	"files": ["*.java"],
  	"detect": None,
  	"replace": [
  		(r"org\.acegissecurity", r"org\.springframework\.security")
  	},
  	"sourceChange": True
  },
  "groovy": {
  	"dependency": {
      "artifactId": "groovy-support-plugin", 
      "groupId": "org.hudsonci.plugins", 
      "version": "3.0.3"
  	},
  	"files": ["*.java"],
  	"detect": ["org\.codehaus\.groovy\."],
  	"replace:" None,
  	"sourceChange": False
  },
  "Jenkins": {
  	"dependency": None,
  	"files": ["*.html", "*.jelly", "*.properties"],
  	"detect": None,
  	"replace": {
  		(r"Jenkins", r"Hudson")
  	},
  	"sourceChange": False
  }
}

_grepscript = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'grep.bash')
_replacescript = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'replace.bash')

def _detect(files, patterns):
	for file in files:
		for pattern in patterns:
			sub = subprocess.Popen([_grepscript, file, pattern], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
			if sub.wait() == 0:
				return True
	return False

def _replace(files, pairs):
	patterns = pairs[:,0]
	for file in files:
		matched = set()
		for pattern in patterns:
			sub = subprocess.Popen([grepscript, files, pattern], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
			if sub.wait() == 0:
				matched.add(pattern)
		if len(matched) > 0:
			for pair in pairs:
				if pair[0] in matched:
					sub = subprocess.Popen([replacescript, files, pair[0], pair[1]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
					if sub.wait() != 0:
						print 'Failed to replace "%s" with "%s"'%(pair[0], pair[1])
			return True
	return False

def _addresult(result, value):
	result[key] = r = {}
	r['dependency'] = value['dependency']
	r['sourceChange'] = value['sourceChange']

def fixsource():
	result = {}
	for key, value in _data.items():
		patterns = value['detect']
		if patterns and _detect(value['files'], patterns):
			_addresult(result, value)
			break
		pairs = value['replace']
		if pairs and _replace(value['files'], pairs):
			_addresult(result, value)
			break
	return result

if __name__ == '__main__':
	result = fixsource()
	dumpAsJson('fixsource.json', result)
	
