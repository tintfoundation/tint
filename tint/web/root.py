from twisted.web import resource

from tint.log import Logger
from tint.web.api import WebAPI

log = Logger(system="TintWeb")


class WebRoot(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.putChild('api', WebAPI(peerServer))
