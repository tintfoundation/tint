import json

from tint.log import Logger

log = Logger(system="TintWebAPI")


class Request(object):
    def __init__(self, req):
        self.req = req

    def jsonPayload(self, name, default=None):
        return json.loads(self.req.content.getvalue()).get(name, default)

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
        obj = { 'successful': False, 'error': str(error) }
        self.renderJSON(obj, response_code=500)

    def renderSuccess(self, result):
        obj = { 'successful': True, 'result': result }
        self.renderJSON(obj)

    def renderJSON(self, result, **kwargs):
        self.render(json.dumps(result), **kwargs)

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
