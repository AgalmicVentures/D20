
import cherrypy
import io

import application.json_application

class D20Application:

	def __init__(self):
		self.json = json_application.D20JsonApplication()

		with io.open('./templates/index.html') as indexTemplateFile:
			self.indexTemplate = indexTemplateFile.read()

	@cherrypy.expose
	def index(self):
		return self.indexTemplate % {
			'title': 'Home',
		}

	@cherrypy.expose
	def default(self, *args, **kwargs):
		return '<html><body><h1>D20 - Page Not Found</h1></body></html>'
