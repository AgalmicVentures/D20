#!/usr/bin/env python3

import cherrypy
import sys

import application

def main():
	print('Starting up D20...')

	cherrypy.config.update({
		'server.socket_host': '0.0.0.0',
		'server.socket_port': 27184,
	})

	d20 = application.D20Application()
	cherrypy.quickstart(d20)

	print('Shutting down D20...')
	return 0

if __name__ == '__main__':
	sys.exit(main())
