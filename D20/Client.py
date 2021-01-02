#!/usr/bin/env python3

# Copyright (c) 2015-2021 Agalmic Ventures LLC (www.agalmicventures.com)
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
try:
	import ujson as json
except ImportError:
	import json
import os
import random
import socket
import struct
import subprocess
import sys
import time
import urllib.parse

##### Defaults #####

#Also updated in Server.py (not shared to avoid path issues)
API_VERSION = '1'

START_WAIT_MAX = 15
STEP_WAIT_MAX = 2

##### Helpers #####

ENTROPY_COUNT_FILE = '/proc/sys/kernel/random/entropy_avail'
RNDADDENTROPY = 0x40085203

def randomSleep(maxSec):
	"""
	Sleeps for up to maxSec seconds.

	:param maxSec: float
	"""
	time.sleep(maxSec * random.random())

def getUrl(url):
	"""
	A helper to do an HTTP GET without requiring 3rd party libraries.

	:param url: str The URL to GET.
	:return: str
	"""
	responseStr = subprocess.check_output(['curl', '-s', url])
	if responseStr is None:
		return None
	return responseStr.decode('utf-8')

##### Application #####

def main(argv=None):
	"""
	The main function of this script.

	:param argv: List[str] Arguments to parse (default sys.argv)
	:return: int
	"""
	parser = argparse.ArgumentParser(description='Roll Some D20.')
	parser.add_argument('--max-entropy', type=int, default=2048,
		help='Maximum entropy in the pool to still roll (default 2048).')
	parser.add_argument('--max-timestamp-deviation', type=float, default=10.0,
		help='Maximum server-client timestamp deviation in seconds (default 10s).')
	parser.add_argument('--strict', action='store_true',
		help='Quit with an error if any of the servers fail.')
	parser.add_argument('--check-local', action='store_true',
		help='Check that it is not a local server being queried.')
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

	#Get the local public IP address
	if arguments.check_local:
		#TODO: figure out a better way to do this
		localIp = getUrl('https://icanhazip.com/')
	else:
		localIp = None

	with open('/dev/random', mode='wb') as devRandom:
		failed = False
		for server in arguments.servers:
			if localIp is not None:
				urlParts = urllib.parse.urlparse(server)
				serverHost, _ = urllib.parse.splitport(urlParts.netloc)
				serverIp = socket.gethostbyname(serverHost)
				if serverIp == localIp:
					print('Skipping %s -- it is the local host' % server)
					continue

			print('Seeding from %s' % server)

			#Calculate the hash of the highest resolution time available as a challenge (%N is nanos for GNU date)a
			now = datetime.datetime.utcnow()
			nowStr = now.strftime('%Y-%m-%dT%H:%M:%S.%f')
			challenge = hashlib.sha512(nowStr.encode('utf-8')).hexdigest() # @suppress This is sufficient for its purpose here right now

			#Query the server and check the challenge response
			#NOTE: Using curl rather than requests to skip the dependency
			responseStr = getUrl(os.path.join(server, 'api/entropy?challenge=%s' % challenge))
			if responseStr is None:
				print('Got no response from %s' % server)
				continue

			try:
				response = json.loads(responseStr)
			except ValueError:
				print('Error parsing JSON from %s' % server)
				continue

			#Check the API version
			responseApiVersion = response['apiVersion']
			if responseApiVersion == API_VERSION:
				#Check the challenge response
				responseTime = response['time']
				expectedChallengeResponse = hashlib.sha512((challenge + responseTime).encode('utf-8')).hexdigest() # @suppress This is sufficient for its purpose here right now
				challengeResponse = response['challengeResponse']
				if challengeResponse == expectedChallengeResponse:
					#Check the freshness of the timestamp
					parsedResponseTime = datetime.datetime.strptime(responseTime, '%Y-%m-%dT%H:%M:%S')
					if abs((now - parsedResponseTime).total_seconds()) < arguments.max_timestamp_deviation:
						#TODO: Pass through something to complicate writing a malicious server
						entropyHex = response['entropy']
						entropy = binascii.unhexlify(entropyHex)

						#Check that not too much entropy is being put in the pool
						if isLinux:
							try:
								with open(ENTROPY_COUNT_FILE) as entropyCountFile:
									entropyAvailable = int(entropyCountFile.read()[:-1])
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
						failed = True
				else:
					print('Invalid challenge response (got %s, expected %s)' % (challengeResponse, expectedChallengeResponse))
					failed = True
			else:
				print('Invalid API version (got %s, expected %s)' % (responseApiVersion, EXPECTED_API_VERSION))
				failed = True

			randomSleep(STEP_WAIT_MAX)

		#Return a failure, if one happened
		if arguments.strict and failed:
			return 1

	return 0

if __name__ == '__main__':
	sys.exit(main())
