
import binascii
import cherrypy
from datetime import datetime
import hashlib
import io
import json

def jsonResponse(value):
	cherrypy.response.headers['Content-Type'] = 'application/json'
	return json.dumps(value, indent=4, sort_keys=True).encode('utf8')

class D20JsonApplication:

	def __init__(self):
		self.urandom = io.open('/dev/urandom', 'rb')

	@cherrypy.expose
	def default(self, *args, **kwargs):
		return jsonResponse({
			'error': 'API not found',
		})

	#TODO: challenge-response
	@cherrypy.expose
	def entropy(self, challenge='', **kwargs):
		if challenge == '':
			return jsonResponse({
				'error': 'No challenge provided',
			})

		h = hashlib.sha512()
		h.update(challenge.encode('utf8', 'ignore'))
		challengeResponse = binascii.hexlify(h.digest()).decode('utf8')

		#Get entropy, throwing away the first and last 8 bytes
		entropy = self.urandom.read(80)
		h.update(entropy[8:-8])
		entropyValue = binascii.hexlify(h.digest()).decode('utf8')

		now = datetime.now()
		nowStr = now.strftime('%Y-%m-%d %H:%M:%S')

		return jsonResponse({
			'challengeResponse': challengeResponse,
			'entropy': entropyValue,
			'time': nowStr,
		})
