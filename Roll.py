#!/usr/bin/env python3

# Copyright (c) 2015-2018 Agalmic Ventures LLC (www.agalmicventures.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import binascii
import datetime
import fcntl
import hashlib
import json
import os
import random
import struct
import subprocess
import sys
import time

EXPECTED_API_VERSION = '1'

START_WAIT_MAX = 15
STEP_WAIT_MAX = 2

ENTROPY_COUNT_FILE = '/proc/sys/kernel/random/entropy_avail'
RNDADDENTROPY = 0x40085203

def randomSleep(maxSec):
	"""
	Sleeps for up to maxSec seconds.

	:param maxSec: float
	"""
	time.sleep(maxSec * random.random())

def main(argv=None):
	parser = argparse.ArgumentParser(description='Roll Some D20.')
	parser.add_argument('--max-entropy', type=int, default=2048,
		help='Maximum entropy in the pool to still roll.')
	parser.add_argument('servers', nargs='*',
		help='Servers to seed the entropy pool from.')

	if argv is None:
		argv = sys.argv
	arguments = parser.parse_args(argv[1:])

	if len(arguments.servers) == 0:
		arguments.servers = ['https://www.agalmicventures.com:8443']

	randomSleep(START_WAIT_MAX)

	#Some features are only available on Linux
	uname = os.uname()
	isLinux = uname.sysname == 'Linux'
	isRoot = os.getuid() == 0

	with open("/dev/random", mode='wb') as devRandom:
		for server in arguments.servers:
			print('Seeding from %s' % server)

			#Calculate the hash of the highest resolution time available as a challenge (%N is nanos for GNU date)a
			now = datetime.datetime.utcnow()
			nowStr = now.strftime('%Y-%m-%dT%H:%M:%S.%f')
			challenge = hashlib.sha512(nowStr.encode('utf-8')).hexdigest()

			#Query the server and check the challenge response
			#NOTE: Using curl rather than requests to skip the dependency
			responseStr = subprocess.check_output(['curl', '-s', '%s/api/entropy?challenge=%s' % (server, challenge)])
			if responseStr is None:
				print('Got no response from %s' % server)
				continue
			responseStr = responseStr.decode('utf-8')

			try:
				response = json.loads(responseStr)
			except ValueError:
				print('Error parsing JSON from %s' % server)
				continue

			#Check the API version
			responseApiVersion = response['apiVersion']
			if responseApiVersion == EXPECTED_API_VERSION:
				#Check the challenge response
				responseTime = response['time']
				expectedChallengeResponse = hashlib.sha512((challenge + responseTime).encode('utf-8')).hexdigest()
				challengeResponse = response['challengeResponse']
				if challengeResponse == expectedChallengeResponse:
					#Check the freshness of the timestamp
					parsedResponseTime = datetime.datetime.strptime(responseTime, '%Y-%m-%dT%H:%M:%S')
					if abs((now - parsedResponseTime).total_seconds()) < 10.0:
						#TODO: Pass through something to complicate writing a malicious server
						entropyHex = response['entropy']
						entropy = binascii.unhexlify(entropyHex)

						#Check that not too much entropy is being put in the pool
						if isLinux:
							try:
								entropyAvailable = int(open(ENTROPY_COUNT_FILE).read()[:-1])
								if entropyAvailable >= arguments.max_entropy:
									print('Available entropy %d over threshold, exiting' % entropyAvailable)
									break
							except (IOError, ValueError):
								pass #Ignore this check if the file can't be read

						#Increment the entropy counter as root
						if isLinux and isRoot:
							#See http://man7.org/linux/man-pages/man4/random.4.html
							entropyBytes = len(entropy)
							entropyBits = entropyBytes * 8 // 64 #Divide by 64 to be conservative
							entropyBitsConservative = min(entropyBits, 64) #Only allow 64 bits total
							randPoolInfo = struct.pack("ii32s", entropyBitsConservative, len(entropy), entropy)
							result = fcntl.ioctl(devRandom, RNDADDENTROPY, randPoolInfo)
						else:
							devRandom.write(entropy)
						print('Success.')
					else:
						print('Timestamp not fresh (got %s vs %s)' % (responseTime, now))
				else:
					print('Invalid challenge response (got %s, expected %s)' % (challengeResponse, expectedChallengeResponse))
			else:
				print('Invalid API version (got %s, expected %s)' % (responseApiVersion, EXPECTED_API_VERSION))

			randomSleep(STEP_WAIT_MAX)

	return 0

if __name__ == '__main__':
	sys.exit(main())
