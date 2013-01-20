import subprocess, sys, os, shutil

def cmd(args):
	if subprocess.call(args):
		print 'FAILED: '+' '.join(args)
		sys.exit(1)

def cmds(str):
	cmd(str.split(' '))
	
def freshdir(path):
	if os.path.exists(path):
		shutil.rmtree(path, True)
	cmd(['mkdir', path])
