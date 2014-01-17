from twisted.web import resource
from twisted.web._responses import BAD_REQUEST

from tint.log import Logger

log = Logger(system="TintWebAPI")


class BadRequest(resource.ErrorPage):
    def __init__(self):
        resource.ErrorPage.__init__(self, BAD_REQUEST, "Bad Request", "Request malformed.")


class WebAPI(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.putChild('v1', APIVersionOne(peerServer))


class APIVersionOne(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.putChild('storage', StorageResource(peerServer))


class StorageResource(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.peerServer = peerServer

    def getParam(self, req, name, default=None):
        return req.args.get(name, [default])[0]

    def render(self, req):
        method = self.getParam(req, 'method')
        if method == 'get':
            return self.getMethod(req)
        elif method == 'set':
            return self.setMethod(req)
        elif method == 'incr':
            return self.incrMethod(req)
        req.setResponseCode(404)
        return ""

    def setMethod(self, req):
        key = self.getParam(req, 'key')
        value = self.getParam(req, 'value')
        if key is None or value is None:
            req.setResponseCode(404)
            return ""
        self.storage[key] = value
        return ""

    def getMethod(self, req):
        key = self.getParam(req, 'key')
        if key is None:
            req.setResponseCode(404)
            return ""
        return self.storage.get(key, "")

    def incrMethod(self, req):
        key = self.getParam(req, 'key')
        #value = self.getParam('value', 1)
        if key is None:
            req.setResponseCode(404)
            return ""
        return self.storage.incr(key)
