import sys
import os

from kitt.interfaces import implements, IDroneDService
from twisted.application import internet
from twisted.application.service import Service
from twisted.web import server, resource, wsgi, static
from kitt.util import dictwrapper
from droned.logging import logWithContext
from django.core.handlers.wsgi import WSGIHandler
import config

class Django(object):
    implements(IDroneDService) 
 
    parentService = None
    service = None 
    SERVICENAME = 'django' 
    SERVICECONFIG = dictwrapper({})

    def install(self, _parentService):
        if hasattr(config.reactor, 'getThreadPool'):
            config.reactor.threadpool = config.reactor.getThreadPool()
        self.parentService = _parentService
 
    def start(self):
        if self.running(): return

        # Set up the Paths
        sys.path.insert(0, self.SERVICECONFIG.DJANGO_ROOT)
        os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' %(self.SERVICECONFIG.APP_NAME)

        # Create the WSGI Pool from Reactor Threadpool
        wsgi_root = wsgi.WSGIResource(config.reactor, config.reactor.threadpool, WSGIHandler())
        root = Django.Root(wsgi_root)

        # Everybody Loves Static Files
        root.putChild("static", static.File(self.SERVICECONFIG.STATIC_ROOT))

        # Install in the Reactor
        main_site = server.Site(root)
        self.service = internet.TCPServer(self.SERVICECONFIG.PORT, main_site)
        self.service.setServiceParent(self.parentService)

    def stop(self):
        if self.service:
            self.service.disownServiceParent()
            self.service.stopService()
            self.service = None
 
    def running(self):
        return bool(self.service) and self.service.running

    class Root(resource.Resource):
        def __init__(self, wsgi_resource):
            resource.Resource.__init__(self)
            self.wsgi_resource = wsgi_resource

        def getChild(self, path, request):
            path0 = request.prepath.pop(0)
            request.postpath.insert(0, path0)
            return self.wsgi_resource
 
log = logWithContext(type=Django.SERVICENAME)
