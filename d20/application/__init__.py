
import cherrypy
import io
import qrcode
import qrcode.constants
import qrcode.image.svg

class D20Application:

	def __init__(self):
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
