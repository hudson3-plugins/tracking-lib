import json

def loadFromJson(filename):
	f = open(filename, 'r')
	object = json.load(f)
	f.close()
	return object

def dumpAsJson(filename, array):
	dump = json.dumps(array, sort_keys = True, indent = 4)
	f = open(filename, 'w')
	f.write(dump)
	f.close()

