#!/usr/bin/env python3

import argparse
import cherrypy
import sys

import Application

def secureHeaders():
    cherrypy.response.headers['X-Frame-Options'] = 'DENY'
    cherrypy.response.headers['X-XSS-Protection'] = '1; mode=block'
    cherrypy.response.headers['Content-Security-Policy'] = "default-src='self'"

cherrypy.tools.secureHeaders = cherrypy.Tool('before_finalize', secureHeaders)

def main():
	parser = argparse.ArgumentParser(description='D20 Entropy Microservice')
	parser.add_argument('-s', '--seed', action='store_true', help='Seed the entropy pool with hashed data from requests.')
	arguments = parser.parse_args(sys.argv[1:])

	print('Starting up D20...')

	d20 = Application.D20Application(arguments.seed)
	cherrypy.quickstart(d20, config='server.conf')

	print('Shutting down D20...')
	return 0

if __name__ == '__main__':
	sys.exit(main())
