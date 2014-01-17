from twisted.internet import reactor

from tint.ssl.context import PFSContextFactory
from tint.log import Logger

from tint.protocols.tintp import ConnectionPool
from tint.protocols.tintp import TintProtocolFactory

class Peer(object):
    def __init__(self, keyStore, resolver):
        self.keyStore = keyStore
        self.resolver = resolver
        self.contextFactory = PFSContextFactory(self.keyStore)        
        self.pool = ConnectionPool(self.resolver, self.contextFactory, self.keyStore)
        self.protocolFactory = TintProtocolFactory(self.pool)

    def listen(self, port, **kwargs):
        reactor.listenSSL(port, self.protocolFactory, self.contextFactory, **kwargs)

    def set(self, keyId, skey, svalue):
        return self.pool.send(keyId, 'set', skey, svalue)
