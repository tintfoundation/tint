import json

from twisted.web import resource
from twisted.web._responses import BAD_REQUEST, BAD_GATEWAY
from twisted.web.server import NOT_DONE_YET

from tint.web.utils import Request
from tint.log import Logger
from tint.apps import AppsList
from tint.storage.addressing import TintURI

log = Logger(system="TintWebAPI")


class BadRequest(resource.ErrorPage):
    def __init__(self):
        resource.ErrorPage.__init__(self, BAD_REQUEST, "Bad Request", "Request malformed.")


class BadGateway(resource.ErrorPage):
    def __init__(self, msg):
        resource.ErrorPage.__init__(self, BAD_GATEWAY, "Bad Gateway", msg)


class WebAPI(resource.Resource):
    def __init__(self, peerServer, appsdir):
        resource.Resource.__init__(self)
        self.putChild('v1', APIVersionOne(peerServer, appsdir))


class APIVersionOne(resource.Resource):
    def __init__(self, peerServer, appsdir):
        resource.Resource.__init__(self)
        self.putChild('storage', StorageResource(peerServer))
        self.putChild('keys', KeysResource(peerServer))
        self.putChild('permissions', PermissionsResource(peerServer))
        self.putChild('apps', AppsResource(peerServer, appsdir))


class APIResource(resource.Resource):
    def __init__(self, peerServer):
        resource.Resource.__init__(self)
        self.peerServer = peerServer
        self.myId = self.peerServer.getKeyId()
        self.log = Logger(system=self)


class APIResourceWithPath(APIResource):
    def getChild(self, path, request):
        return self

    def getStoragePath(self, req):
        return "/" + "/".join(req.path.split('/')[4:])

    def getKeyURI(self, req):
        uri = "tint://%s" % self.getStoragePath(req)[1:]
        return TintURI(uri)


class PermissionsResource(APIResourceWithPath):
    def render_GET(self, req):
        uri = self.getStoragePath(req)
        wreq = Request(req)
        requestor = wreq.getParam('as', self.myId)
        access = self.peerServer.storage.accessAvailable(requestor, uri)
        req.setHeader('content-type', "application/json")
        return json.dumps(access)


    def render_POST(self, req):
        uri = self.getStoragePath(req)
        wreq = Request(req)
        requestor = wreq.getParam('as', self.myId)
        optype = wreq.getParam('optype', '*')
        self.peerServer.storage.grantAccess(requestor, uri, optype)
        access = self.peerServer.storage.accessAvailable(requestor, uri)
        req.setHeader('content-type', "application/json")
        return json.dumps(access)


class AppsResource(APIResource):
    def __init__(self, peerServer, appsdir):
        APIResource.__init__(self, peerServer)
        self.apps = AppsList(appsdir)

    def render_GET(self, req):
        req.setHeader('content-type', "application/json")
        return json.dumps([ {'name': name} for name in self.apps.getAppNames() ])


class KeysResource(APIResource):
    def render_GET(self, req):
        result = { 'mykey': { 'id': self.peerServer.getKeyId(),
                              'key': str(self.peerServer.getPublicKey()) },
                   'authorized_keys': [ f.__dict__ for f in self.peerServer.friends ] }
        req.setHeader('content-type', "application/json")
        return json.dumps(result)

    def render_POST(self, req):
        wreq = Request(req)
        name = wreq.getParam('name')
        keyid = wreq.getParam('keyid')
        result = self.peerServer.friends.addFriendById(name, keyid)
        result.addCallback(wreq.renderJSON)
        result.addErrback(wreq.renderError)
        return NOT_DONE_YET

    def render_DELETE(self, req):
        wreq = Request(req)
        result = self.peerServer.friends.removeFriend(wreq.getParam('name'))
        req.setHeader('content-type', "application/json")
        return json.dumps({ 'result': result })


class StorageResource(APIResourceWithPath):
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

    def render_POST(self, req):
        uri = self.getKeyURI(req)
        wreq = Request(req)
        value = wreq.getParam('value', '')
        if wreq.isDir():
            result = self.peerServer.push(uri.host, str(uri.path), value)
        else:
            result = self.peerServer.set(uri.host, str(uri.path), value)
        result.addCallback(wreq.renderJSON)
        result.addErrback(wreq.renderError)
        return NOT_DONE_YET
