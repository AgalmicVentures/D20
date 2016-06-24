
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
