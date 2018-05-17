#!/opt/stack/bin/python3 -E
#
# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
#

import subprocess
import random
import time
import os
import json
from stack.util import get_interfaces


debug = open('/tmp/stacki-profile.debug', 'w')

for i in os.environ:
	debug.write('%s %s\n' % (i, os.environ[i]))	

debug.close()

#
# make sure the target directory is there
#
try:
	os.makedirs('/tmp/profile')
except:
	pass


# to include IB information, load ib_ipoib driver
subprocess.call(["/sbin/modprobe","ib_ipoib"])
#
# get the interfaces
#

interface_number = 0

curlcmd = [ '/usr/bin/curl', '-s', '-w', '%{http_code}', '--local-port', '1-100',
	'--output', '/tmp/stacki-profile.xml', '--insecure' ]


for interface, hwaddr in get_interfaces():
	if interface and hwaddr:
		curlcmd.append('--header')
		curlcmd.append('X-RHN-Provisioning-MAC-%d: %s %s' % (interface_number, interface, hwaddr))
		interface_number += 1

#
# get the number of CPUs
#
numcpus = 0
f = open('/proc/cpuinfo', 'r')
for line in f.readlines():
	l = line.split(':')
	if l[0].strip() == 'processor':
		numcpus += 1
f.close()

server = os.environ.get('Server', None)
if not server:
	cmdline = open('/proc/cmdline', 'r')
	cmdargs = cmdline.readline()
	cmdline.close()

	for cmdarg in cmdargs.split():
		l = cmdarg.split('=')
		if l[0].strip() == 'Server':
			server = l[1]

if not server:
	# No server found on boot line, so maybe we are in AWS and can find
	# it from the user-data json.
	p = subprocess.Popen([ '/usr/bin/curl', 'http://169.254.169.254/latest/user-data' ],
			     stdout=subprocess.PIPE,
			     stderr=subprocess.PIPE)
	o, e = p.communicate()
	try:
		data = json.loads(o)
	except:
		data = {}
	server = data.get('master')


request = 'https://%s/install/sbin/profile.cgi?os=sles&arch=x86_64&np=%d' % \
	(server, numcpus)
curlcmd.append(request)

#
# retry until we get an installation file. if the HTTP request fails, then sleep
# for a random amount of time (between 3 and 10 seconds) before we retry.
#
http_code = 0
while http_code != 200:
	p = subprocess.Popen(curlcmd, stdout=subprocess.PIPE, stderr=open('/dev/null'))

	try:
		http_code = int(p.stdout.readline())
	except:
		http_code = 0

	if http_code != 200:
		time.sleep(random.randint(3, 10))

