import subprocess
from cmpversion import *

_debug = False

def resetToHighTag():
	p = subprocess.Popen(['git', 'tag'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	tags = []
	while True:
		line = p.stdout.readline()
		if not line:
			break
		tags.append(line.strip())
	if p.wait() == 0:
		if _debug: print tags
		max = 'max'
		for tag in tags:
			if cmpversion(max, tag) < 0:
				max = tag
		if _debug: print max
		if max != 'max':
			if not subprocess.call(['git', 'reset', '--hard', max]):
				if _debug: print max
				return max
	if _debug: print 'Failed'
	return None
