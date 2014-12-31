import json

from twisted.web import resource
from twisted.web._responses import BAD_REQUEST, BAD_GATEWAY
from twisted.web.server import NOT_DONE_YET

from tint.log import Logger
from tint.storage.addressing import TintURI

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
        # storage, keys, permissions, apps should be the only endpoints really
        self.putChild('storage', StorageResource(peerServer))
        self.putChild('keys', KeysResource(peerServer))


class Request(object):
    def __init__(self, req):
        self.req = req

    def getParam(self, name, default=None):
        return self.req.args.get(name, [default])[0]

    def isDir(self):
        return self.req.path[-1] == '/'

    def setHead(self, response_code=200, content_type="text/javascript"):
        self.req.setHeader('server', 'tint web')
        self.req.setHeader('content-type', "%s; charset=UTF-8" % content_type)
        if response_code != 200:
            self.req.setResponseCode(response_code)

    def renderError(self, error):
        self.renderJSON({ 'error': str(error) })

    def renderJSON(self, result):
        self.render(json.dumps(result))

    def render(self, value=None, response_code=200, content_type="text/javascript"):
        value = value or ""
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        callback = self.getParam('callback')
        if content_type == "text/javascript" and callback is not None:
            value = "%s(%s)" % (callback, value)
        self.setHead(response_code, content_type)
        log.info("writing: %s" % value)
        try:
            self.req.write(value)
            self.req.finish()
        except RuntimeError, e:
            log.warning("Connection lost.  Did not write JS response: %s" % str(e))


class KeysResource(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.peerServer = peerServer

    def render_GET(self, req):
        keys = []
        for key in self.peerServer.keyStore.getAuthorizedKeysList():
            keys.append({ 'id': key.getKeyId(), 'name': key.name, 'key': str(key) })
        result = { 'mykey':
                   { 'id': self.peerServer.getKeyId(),
                     'key': str(self.peerServer.getPublicKey()) },
                   'authorized_keys': keys }
        req.setHeader('content-type', "application/json")
        return json.dumps(result)

    def render_POST(self, req):
        wreq = Request(req)
        name = wreq.getParam('name')
        keyid = wreq.getParam('keyid')
        try:
            self.peerServer.addFriendById(name, keyid)
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
        wreq = Request(req)
        if wreq.isDir():
            offset = int(wreq.getParam('offset', 0))
            length = int(wreq.getParam('length', 100))
            result = self.peerServer.ls(uri.host, str(uri.path), offset, length)
        else:
            result = self.peerServer.get(uri.host, str(uri.path))
        result.addCallback(wreq.renderJSON)
        result.addErrback(wreq.renderError)
        return NOT_DONE_YET

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
