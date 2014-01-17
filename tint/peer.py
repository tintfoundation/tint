from tint.ssl.context import PFSContextFactory
from tint.log import Logger

from tint.protocols.tintp import ConnectionPool
from tint.protocols.tintp import TintProtocolFactory


class Peer(object):
    def __init__(self, keyStore, storage, resolver):
        self.keyStore = keyStore
        self.storage = storage
        self.resolver = resolver
        self.contextFactory = PFSContextFactory(self.keyStore)
        self.pool = ConnectionPool(self.resolver, self.contextFactory, self.keyStore, self.storage)
        self.protocolFactory = TintProtocolFactory(self.pool)
        self.log = Logger(system=self)

    def set(self, keyId, skey, svalue):
        # hey, that's me!
        if keyId == self.keystore.getKeyId():
            return self.storage.set(keyId, skey, svalue)
        return self.pool.send(keyId, 'set', skey, svalue)

    def get(self, keyId, skey):
        # hey, that's me!
        if keyId == self.keystore.getKeyId():
            return self.storage.get(keyId, skey)
        return self.pool.send(keyId, 'get', skey)

    def incr(self, keyId, skey, amount=1, default=0):
        # hey, that's me!
        if keyId == self.keystore.getKeyId():
            return self.storage.incr(keyId, skey, amount, default)
        return self.pool.send(keyId, 'incr', skey, amount, default)
