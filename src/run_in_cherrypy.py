from cherrypy import wsgiserver
from website_runner import app

d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 80), d)

if __name__ == '__main__':
    try:
	print "running server..."
        server.start()
    except KeyboardInterrupt:
        server.stop()
