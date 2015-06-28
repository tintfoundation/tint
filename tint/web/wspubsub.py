from collections import defaultdict
import json
import random

from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

from tint.log import Logger
log = Logger(system="TintWebSockets")


class MSGTYPES:
    HELLO = 1
    WELCOME = 2
    ABORT = 3
    CHALLENGE = 4
    AUTHENTICATE = 5
    GOODBYE = 6
    ERROR = 8
    PUBLISH = 16
    PUBLISHED = 17
    SUBSCRIBE = 32
    SUBSCRIBED = 33
    UNSUBSCRIBE = 34
    UNSUBSCRIBED = 35
    EVENT = 36


class WAMPMessage(object):
    def __init__(self, typeid, *args):
        self.typeid = typeid
        self.args = list(args)
        self.typename = None
        for name in filter(lambda s: s.isupper(), dir(MSGTYPES)):
            if getattr(MSGTYPES, name) == self.typeid:
                self.typename = name


    def getArg(self, partno, default=None):
        if partno >= len(self.args):
            return default
        return self.args[partno]


    def __str__(self):
        name = self.typename or str(self.typeid)
        args = map(str, self.args)
        return "[%s %s]" % (name, ", ".join(args))


    def encode(self):
        return json.dumps([self.typeid] + self.args)


    @classmethod
    def decode(self, msg):
        msg = json.loads(msg.decode('utf8'))
        return WAMPMessage(*msg)


class WebSocketProtocol(WebSocketServerProtocol):
    def __init__(self, *args, **kwargs):
        super(WebSocketServerProtocol, self).__init__(*args, **kwargs)
        self.eventid = 0


    def onConnect(self, request):
        self.client = request.peer
        log.debug("connection from %s" % self.client)


    def onMessage(self, payload, isBinary):
        if isBinary:
            log.warning("Got a binary message from %s - ignoring" % self.client)
            return

        # call self.onMSGTYPE(message) if it exists
        message = WAMPMessage.decode(payload)
        func = getattr(self, "on%s" % message.typename)
        if message.typename is not None and func is not None:
            log.debug("message from %s: %s" % (self.client, message))
            func(message)
        else:
            log.debug("Unrecognized msg type or no handler function for msg type id %i" % message.typeid)


    def onHELLO(self, msg):
        realm, details = msg.args
        if realm != "tint.storage":
            self.send(MSGTYPES.ABORT, {}, 'wamp.error.no_such_realm')
        else:
            sessionid = random.randint(0, 9007199254740992)
            self.send(MSGTYPES.WELCOME, sessionid, {})


    def onSUBSCRIBE(self, msg):
        rid, options, topic = msg.args
        et = topic.split('.')[-1]
        topics = ['value', 'child_added', 'child_changed']
        if not topic.startswith('tint.storage.event') or et not in topics:
            self.send(MSGTYPES.ERROR, MSGTYPES.SUBSCRIBE, rid, {}, 'wamp.error.invalid_uri')
        else:
            subid = self.factory.storageSubscribe(self.client, options.get('key', '/'), et, self.onStorageEvent)
            self.send(MSGTYPES.SUBSCRIBED, rid, subid)


    def onUNSUBSCRIBE(self, msg):
        rid, subid = msg.args
        if self.factory.storageUnsubscribe(self.client, subid):
            self.send(MSGTYPES.UNSUBSCRIBED, rid)
        else:
            self.send(MSGTYPES.ERROR, MSGTYPES.UNSUBSCRIBE, rid, {}, 'wamp.error.no_such_subscription')


    def onStorageEvent(self, subid, key, value):
        self.eventid += 1
        self.send(MSGTYPES.EVENT, subid, self.eventid, { 'key': key, 'value': value })


    def send(self, *parts):
        msg = WAMPMessage(*parts)
        log.debug("message to %s: %s" % (self.client, msg))
        self.sendMessage(msg.encode(), False)


    def onClose(self, wasClean, code, reason):
        log.debug("connection closed from %s: %s" % (self.client, reason))


class WebSocketRoot(WebSocketServerFactory):
    protocol = WebSocketProtocol

    def __init__(self, peer, url):
        super(WebSocketServerFactory, self).__init__(url, debug=False)
        self.peer = peer
        self.setProtocolOptions(maxConnections=200)
        self.subscriptions = defaultdict(dict)


    def storageSubscribe(self, client, key, etype, func):
        subid = len(self.subscriptions[client])

        def onchange(key, value):
            func(subid, key, value)

        self.peer.storage.subscribe(key, etype, onchange)
        self.subscriptions[client][str(subid)] = (key, etype, onchange)


    def storageUnsubscribe(self, client, subid):
        if client not in self.subscriptions or str(subid) not in self.subscriptions[client]:
            return False
        key, etype, func = self.subscriptions[client][str(subid)]
        self.peer.storage.unsubscribe(key, etype, func)
        return True
