import json

from twisted.web import resource
from twisted.web._responses import BAD_REQUEST, BAD_GATEWAY

from tint.log import Logger
from tint.storage.permanent import TintURI
from tint.ssl.keymagic import PublicKey

log = Logger(system="TintWebAPI")


class BadRequest(resource.ErrorPage):
    def __init__(self):
        resource.ErrorPage.__init__(self, BAD_REQUEST, "Bad Request", "Request malformed.")


class BadGateway(resource.ErrorPage):
    def __init__(self, msg):
        resource.ErrorPage.__init__(self, BAD_GATEWAY, "Bad Gateway", msg)


class WebAPI(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.putChild('v1', APIVersionOne(peerServer))


class APIVersionOne(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.putChild('storage', StorageResource(peerServer))
        self.putChild('keys', KeysResource(peerServer))


class Request(object):
    def __init__(self, req):
        self.req = req

    def getParam(self, name, default=None):
        return self.req.args.get(name, [default])[0]


class KeysResource(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.peerServer = peerServer

    def render_GET(self, req):
        keys = []
        for key in self.peerServer.keyStore.getAuthorizedKeysList():
            keys.append({ 'id': key.getKeyId(), 'key': str(key) })
        result = { 'mykey':
                   { 'id': self.peerServer.getKeyId(),
                     'key': str(self.peerServer.getPublicKey()) },
                   'authorized_keys': keys }
        req.setHeader('content-type', "application/json")
        return json.dumps(result)

    def render_POST(self, req):
        wreq = Request(req)
        key = wreq.getParam('key')
        name = wreq.getParam('name')
        try:
            publicKey = PublicKey(key)
            self.peerServer.keyStore.setAuthorizedKey(publicKey, name)
            return "success"
        except Exception, err:
            return str(err)


class StorageResource(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.peerServer = peerServer
        self.myId = self.peerServer.getKeyId()

    def getChild(self, path, request):
        return self

    def getKeyURI(self, req):
        uri = "tint://%s" % "/".join(req.path.split('/')[4:])
        return TintURI(uri)

    def render_GET(self, req):
        uri = self.getKeyURI(req)
        result = self.peerServer.get(uri.host, uri.path)
        if result is None:
            return resource.NoResource("key not found").render(req)
        return result

    def render_PUT(self, req):
        wreq = Request(req)
        amount = wreq.getParam('amount', 1)
        default = wreq.getParam('default', 0)
        uri = self.getKeyURI(req)
        result = self.peerServer.incr(uri.host, uri.path, amount, default)
        if result is None:
            return BadGateway("Could not reach %s" % uri.host).render(req)
        return result

    def render_POST(self, req):
        wreq = Request(req)
        data = wreq.getParam('data', "")
        uri = self.getKeyURI(req)
        if not self.peerServer.set(uri.host, uri.path, data):
            return BadGateway("Could not reach %s" % uri.host).render(req)
        return ""
