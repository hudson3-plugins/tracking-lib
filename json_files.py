import json

def loadFromJson(filename):
	try:
		f = open(filename, 'r')
		object = json.load(f)
		f.close()
		return object
	except IOError:
		return None

def dumpAsJson(filename, array):
	dump = json.dumps(array, sort_keys = True, indent = 4)
	f = open(filename, 'w')
	f.write(dump)
	f.close()

