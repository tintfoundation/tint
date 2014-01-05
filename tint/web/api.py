from twisted.web import resource

from tint.log import Logger

log = Logger(system="TintWebAPI")

class WebAPI(resource.Resource):
    def __init__(self, storage):
        resource.Resource.__init__(self)
        self.putChild('v1', APIVersionOne(storage))


class APIVersionOne(resource.Resource):
    def __init__(self, storage):
        resource.Resource.__init__(self)
        self.storage = storage

    def render(self, req):
        return "Hi!"
