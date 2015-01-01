import os

from twisted.web import resource, static
from twisted.web.util import Redirect

from tint.log import Logger
from tint.web.api import WebAPI
import tint.web

log = Logger(system="TintWeb")


class WebRoot(resource.Resource):
    def __init__(self, peerServer, appsdir):
        resource.Resource.__init__(self)
        self.putChild('api', WebAPI(peerServer, appsdir))
        self.putChild('apps', static.File(appsdir)) #os.path.join(tint.web.__path__[0], "apps")))

    def getChild(self, path, request):
        if path == '':
            return Redirect("/apps/admin")
        return resource.Resource.getChild(self, path, request)
