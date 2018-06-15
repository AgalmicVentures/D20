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
from Crypto.Cipher import AES
from Crypto.Util import Counter
import datetime
import flask
import hashlib
import os
import sys

##### Defaults #####

#Default TCP port
DEFAULT_PORT = 27184

#Size of entropy in 32 byte (256 bit) blocks
DEFAULT_ENTROPY_SIZE = 16 * 32

#How often to reseed the DRBG
DEFAULT_RESEED_INTERVAL = 1024 * 1024

##### Application #####

class RandomBitGenerator(object):

	def __init__(self, arguments):

		self._reseedInterval = arguments.reseed_interval
		self._seedEntropy = arguments.seed_urandom
		self._zeroBlock = b'\x00' * arguments.entropy_size

		#OS randomness to use for seeds
		if self._seedEntropy:
			self._urandom = open('/dev/urandom', 'wb')

		self.reseed()

	def reseed(self):
		"""
		Reseeds the internal AES-256-CTR-DRBG.
		"""
		secret = os.urandom(32) #256 bits @suppress
		iv = os.urandom(16)

		counter = Counter.new(128, initial_value=int.from_bytes(iv, byteorder='little'))
		self._cipher = AES.new(secret, AES.MODE_CTR, counter=counter)
		self._n = 0

	def entropy(self, **kwargs):
		"""
		API to return entropy to a client.
		"""
		#Reseed the DRBG after a while
		self._n += 1
		if self._n >= self._reseedInterval:
			self.reseed()

		#Get entropy from an AES-256-CTR-DRBG
		entropy = self._cipher.encrypt(self._zeroBlock)
		return entropy

rbg = None #Assigned in main()

#Setup Flask application
app = flask.Flask('D20')

##### Basic Routes #####

@app.errorhandler(404)
def error404(e):
	return ''.join([
		'<html><body>',
		'<h1>D20 - Page Not Found</h1>',
		'<p>The only endpoint available on this entropy micro-service is <a href="/api/entropy">/api/entropy</a>.</p>',
		'<p>For more information including the complete source code, visit <a href="https://github.com/AgalmicVentures/D20">the D20 repository</a>.</p>',
		'</body></html>',
	]), 404

##### API Routes #####

api = flask.Blueprint('api', __name__)

@api.route('/entropy', methods=['GET', 'POST'])
def entropy():
	"""
	API to return entropy to a client.
	"""
	challenge = flask.request.args.get('challenge')
	if challenge is None:
		return flask.jsonify({
			'error': "No 'challenge' parameter provided (e.g. /api/entropy?challenge=0123456789ABCDEF)",
		})
	elif len(challenge) < 8:
		return flask.jsonify({
			'error': "'challenge' parameter provided is too short; must be at least 8 bytes",
		})

	#Get the time
	now = datetime.datetime.utcnow()
	iso8601Format = '%Y-%m-%dT%H:%M:%S'
	nowStr = now.strftime(iso8601Format)

	#Generate the challenge response: the hash of the challenge || time
	h = hashlib.sha512()
	h.update(challenge.encode('utf8', 'ignore'))
	h.update(nowStr.encode('utf8', 'ignore'))
	challengeResponseBytes = binascii.hexlify(h.digest())
	challengeResponse = challengeResponseBytes.decode('utf8')

	#Get entropy from an AES-256-CTR-DRBG
	entropy = rbg.entropy()
	entropyValue = binascii.hexlify(entropy).decode('utf8')

	return flask.jsonify({
		'apiVersion': '1', #Also update in roll.sh
		'challengeResponse': challengeResponse,
		'entropy': entropyValue,
		'time': nowStr,
	})

def main(argv=None):
	parser = argparse.ArgumentParser(description='D20 Entropy Microservice')
	parser.add_argument('-p', '--port', action='store', type=int, default=DEFAULT_PORT,
		help='TCP port to run on.')
	parser.add_argument('-e', '--entropy-size', action='store', type=int, default=DEFAULT_ENTROPY_SIZE,
		help='Size of entropy to return in bytes (default 16 512-bit blocks).')
	parser.add_argument('-r', '--reseed-interval', action='store', type=int, default=DEFAULT_RESEED_INTERVAL,
		help='Reseed the internal DRBG at this frequency (default 2^20).')
	parser.add_argument('-s', '--seed-urandom', action='store_true',
		help='Seed the entropy pool with hashed data from requests.')
	arguments = parser.parse_args(sys.argv[1:])

	#Instantiate the rnadom bit generator
	global rbg
	rbg = RandomBitGenerator(arguments)

	#TODO: productionize
	print('Starting up D20...')
	app.register_blueprint(api, url_prefix='/api')
	app.run(port=arguments.port)
	print('Shutting down D20...')

	return 0

if __name__ == '__main__':
	sys.exit(main())
