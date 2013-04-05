#!/usr/bin/python
import sys, re, os, json
#
# Print top n%. See Usage.
#
# Before printing, clean the data by recalculating percentages based
# on calculated total sites.
#
# Write jinstallpercent, a map from plugin id to percentage. This is
# used by tracking and automation to color results.
#
# The most recent stats may not be from the same date, so there's
# a bit of apples and oranges going on. To mitigate this, we assume
# that the number of installations is correct as of the date it was
# reported, and recalculate the percentage.
#

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

#----------------------------------------------------------
# Clean arguments

if len(sys.argv) < 2:
	print "Usage: ./top.py PERCENT"
	print "Arguments:"
	print "       PERCENT = integer from 0 to 100. Trailing % optional."
	print "                 If 0, nothing is printed."
	print "Side effects:"
	print "       Writes jinstallmap.json. Maps from plugin id to percent of"
	print "       Jenkins sites where plugin is installed."
	sys.exit(1)

arg = sys.argv[1]
if arg.endswith("%"):
	arg = arg[:-1]
top = float(arg)

if top < 0 or top >100:
	print "Percent must be in range 0..100, found %s" % arg
	sys.exit(1)

bot = 100.0 - top

#----------------------------------------------------------
# Convert stats to list for sorting

pstats = loadFromJson("jenkinsstats.json")

lstats = []

for key, value in pstats.items():
	lstats.append([key, value["install"], value["percent"], value["installTS"]])

#----------------------------------------------------------
# Sort by install within installTS to get latest, highest first.

tmp = sorted(lstats, key=lambda t: (t[3], t[1]), reverse=True)

#----------------------------------------------------------
# Calculate total installations.

hitmp = tmp[0]
hiIns = hitmp[1]
hiTS  = hitmp[3]

installations = int(round(100.0*hitmp[1]/hitmp[2]))

#debug
#print installations, "calculated installations"
#print hitmp

#----------------------------------------------------------
# Recalculate percentages, write jinstallpercent.json
# map of plugin id to percentage.

def perc(install):
	return 100.0 * install / installations

# sort by install

slstats = sorted(lstats, key=lambda t: t[1], reverse=True)

jinstallpercent = {}
jinstall = {}
lines = []
for i in range(0,len(slstats)):
	tuple = slstats[i]
	percent = perc(tuple[1])
	if percent >= bot:
		lines.append("{:>3d} {:<40} {:>8d} {:>7.2f}".format(i+1, tuple[0], tuple[1], percent))
	jinstallpercent[tuple[0]] = percent
	jinstall[tuple[0]] = t = {}
	t['num'] = tuple[1]
	t['perc'] = percent

dumpAsJson("jinstallpercent.json", jinstallpercent)
dumpAsJson("jinstall.json", jinstall)

#----------------------------------------------------------
# Print the requested top n%.

if top == 0:
	sys.exit(0)

if len(lines) == 0:
	print "No plugins in top %d%%" % top
else:
	print "Top %d%%:" % top
	print
	print "{:<3} {:<40} {:<8} {:<6}".format("No.", "Plugin", "Installs", "Percent")
	for line in lines:
		print line

		

