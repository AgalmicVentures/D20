
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
import datetime
import hashlib
import io
import json

def jsonResponse(value):
	cherrypy.response.headers['Content-Type'] = 'application/json'
	return json.dumps(value, indent=4, sort_keys=True).encode('utf8')

class D20Application(object):

	def __init__(self, seedEntropy=False):
		self.api = D20ApiApplication(seedEntropy=seedEntropy)

	@cherrypy.expose
	def default(self, *args, **kwargs):
		return ''.join([
			'<html><body>',
			'<h1>D20 - Page Not Found</h1>',
			'<p>The only endpoint available on this entropy micro-service is <a href="/api/entropy">/api/entropy</a>.</p>',
			'<p>For more information including the complete source code, visit <a href="https://github.com/AgalmicVentures/D20">the D20 repository</a>.</p>',
			'</body></html>',
		])

class D20ApiApplication(object):

	def __init__(self, seedEntropy=False):
		self._seedEntropy = seedEntropy
		self._urandom = io.open('/dev/urandom', 'rb')
		if seedEntropy:
			self._urandom_w = io.open('/dev/urandom', 'wb')

	@cherrypy.expose
	def default(self, *args, **kwargs):
		return jsonResponse({
			'error': 'API not found',
		})

	@cherrypy.expose
	def entropy(self, challenge='', **kwargs):
		if challenge == '':
			return jsonResponse({
				'error': "No 'challenge' parameter provided (e.g. /api/entropy?challenge=123)",
			})

		h = hashlib.sha512()
		h.update(challenge.encode('utf8', 'ignore'))
		challengeResponseBytes = binascii.hexlify(h.digest())
		challengeResponse = challengeResponseBytes.decode('utf8')

		#Get entropy from /dev/urandom
		entropy = self._urandom.read(128)
		h.update(entropy)
		entropyValue = binascii.hexlify(h.digest()).decode('utf8')

		now = datetime.datetime.now()
		iso8601Format = '%Y-%m-%dT%H:%M:%S'
		nowStr = now.strftime(iso8601Format)

		#Reseed the entropy pool if necessary
		if self._seedEntropy:
			self._urandom_w.write(challengeResponseBytes)
			self._urandom_w.write(now.strftime('%S.%f').encode('utf8'))

		return jsonResponse({
			'challengeResponse': challengeResponse,
			'entropy': entropyValue,
			'time': nowStr,
		})
