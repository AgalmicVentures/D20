
import cherrypy
import io

import application.json_application

class D20Application:

	def __init__(self):
		self.json = json_application.D20JsonApplication()

	@cherrypy.expose
	def default(self, *args, **kwargs):
		return '<html><body><h1>D20 - Page Not Found</h1></body></html>'
