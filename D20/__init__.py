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
import cherrypy
import sys

import Application

#Size of entropy in 32 byte (256 bit) blocks
DEFAULT_ENTROPY_SIZE = 16 * 32

#How often to reseed the DRBG
DEFAULT_RESEED_INTERVAL = 1024 * 1024

def secureHeaders():
	"""
	Adds HTTP headers for security. This function is not called directly, but
	rather it is invoked by CherryPy as a tool before finalizing the response
	to a request.
	"""
	cherrypy.response.headers['X-Frame-Options'] = 'DENY'
	cherrypy.response.headers['X-XSS-Protection'] = '1; mode=block'
	cherrypy.response.headers['Content-Security-Policy'] = "default-src='self'"

cherrypy.tools.secureHeaders = cherrypy.Tool('before_finalize', secureHeaders)

def main():
	parser = argparse.ArgumentParser(description='D20 Entropy Microservice')
	parser.add_argument('-e', '--entropy-size', action='store', type=int, default=DEFAULT_ENTROPY_SIZE,
		help='Size of entropy to return in bytes (default 16 512-bit blocks).')
	parser.add_argument('-r', '--reseed-interval', action='store', type=int, default=DEFAULT_RESEED_INTERVAL,
		help='Reseed the internal DRBG at this frequency (default 2^20).')
	parser.add_argument('-s', '--seed-urandom', action='store_true',
		help='Seed the entropy pool with hashed data from requests.')
	arguments = parser.parse_args(sys.argv[1:])

	print('Starting up D20...')

	d20 = Application.D20Application(arguments)
	cherrypy.quickstart(d20, config='server.conf')

	print('Shutting down D20...')
	return 0

if __name__ == '__main__':
	sys.exit(main())
