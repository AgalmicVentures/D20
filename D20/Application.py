
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

import binascii
import cherrypy
from Crypto.Cipher import AES
from Crypto.Util import Counter
import datetime
import hashlib
import io
import json
import os

#Size of entropy in 32 byte (256 bit) blocks
#TODO: make this an option
ENTROPY_SIZE = 16 * 32

#How often to reseed the DRBG
#TODO: make this an option, figure out a proper default value, etc.
RESEED_INTERVAL = 1024 * 1024

def jsonResponse(value):
	"""
	Helper to return a JSON blob as an HTTP response by serializing it and setting headers correctly.

	:param value: dict
	:return: str
	"""
	cherrypy.response.headers['Content-Type'] = 'application/json'
	return json.dumps(value, indent=4, sort_keys=True).encode('utf8')

class D20Application(object):

	def __init__(self, seedEntropy=False):
		self.api = D20ApiApplication(seedEntropy=seedEntropy)

	@cherrypy.expose
	def default(self, *args, **kwargs):
		"""
		By default, give a user some instructions, since if they are seeing this, they likely arrived manually.
		"""
		return ''.join([
			'<html><body>',
			'<h1>D20 - Page Not Found</h1>',
			'<p>The only endpoint available on this entropy micro-service is <a href="/api/entropy">/api/entropy</a>.</p>',
			'<p>For more information including the complete source code, visit <a href="https://github.com/AgalmicVentures/D20">the D20 repository</a>.</p>',
			'</body></html>',
		])

class D20ApiApplication(object):

	def __init__(self, seedEntropy=False, entropySize=ENTROPY_SIZE):
		self._seedEntropy = seedEntropy
		self._zeroBlock = b'\x00' * entropySize

		#OS randomness to use for seeds
		if seedEntropy:
			self._urandom = io.open('/dev/urandom', 'wb')

		self._reseed()

	def _reseed(self):
		"""
		Reseeds the internal AES-256-CTR-DRBG.
		"""
		secret = os.urandom(32) #256 bits
		iv = os.urandom(16)

		counter = Counter.new(128, initial_value=int.from_bytes(iv, byteorder='little'))
		self._cipher = AES.new(secret, AES.MODE_CTR, counter=counter)
		self._n = 0

	@cherrypy.expose
	def entropy(self, challenge='', **kwargs):
		"""
		API to return entropy to a client.

		:param challenge: str Containing a challenge value that will be used to prove the recency of the result.
		"""
		if challenge == '':
			return jsonResponse({
				'error': "No 'challenge' parameter provided (e.g. /api/entropy?challenge=0123456789ABCDEF)",
			})
		elif len(challenge) < 8:
			return jsonResponse({
				'error': "'challenge' parameter provided is too short; must be at least 8 bytes",
			})

		#Reseed the DRBG after a while
		self._n += 1
		if self._n >= RESEED_INTERVAL:
			self._reseed()

		#Get the time
		now = datetime.datetime.now()
		iso8601Format = '%Y-%m-%dT%H:%M:%S'
		nowStr = now.strftime(iso8601Format)

		#Generate the challenge response: the hash of the challenge || time
		h = hashlib.sha512()
		h.update(challenge.encode('utf8', 'ignore'))
		h.update(nowStr.encode('utf8', 'ignore'))
		challengeResponseBytes = binascii.hexlify(h.digest())
		challengeResponse = challengeResponseBytes.decode('utf8')

		#Get entropy from an AES-256-CTR-DRBG
		entropy = self._cipher.encrypt(self._zeroBlock)
		entropyValue = binascii.hexlify(entropy).decode('utf8')

		#Reseed the entropy pool if necessary
		if self._seedEntropy:
			self._urandom.write(challengeResponseBytes)
			self._urandom.write(now.strftime('%S.%f').encode('utf8'))

		return jsonResponse({
			'apiVersion': '1', #Also update in roll.sh
			'challengeResponse': challengeResponse,
			'entropy': entropyValue,
			'time': nowStr,
		})

	@cherrypy.expose
	def default(self, *args, **kwargs):
		"""
		By default, all other API calls return an error.
		"""
		return jsonResponse({
			'error': 'API not found',
		})
