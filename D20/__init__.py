#!/usr/bin/env python3

import cherrypy
import sys

import Application

def main():
	print('Starting up D20...')

	d20 = Application.D20Application()
	cherrypy.quickstart(d20, config='server.conf')

	print('Shutting down D20...')
	return 0

if __name__ == '__main__':
	sys.exit(main())
