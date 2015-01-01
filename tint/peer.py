from tint.ssl.context import PFSContextFactory
from tint.log import Logger

from tint.protocols.tintp import ConnectionPool
from tint.protocols.tintp import TintProtocolFactory
from tint.friends import FriendsList


class Peer(object):
    def __init__(self, keyStore, storage, resolver):
        self.keyStore = keyStore
        self.storage = storage
        self.contextFactory = PFSContextFactory(self.keyStore)
        self.pool = ConnectionPool(resolver, self.contextFactory, self.keyStore, self.storage)
        self.protocolFactory = TintProtocolFactory(self.pool)
        self.friends = FriendsList(self.storage, self.keyStore, resolver)
        self.log = Logger(system=self)

    def getKeyId(self):
        """
        Get the keyId used by this peer (this peer's identifier).

        This is stored in the key store.
        """
        return self.keyStore.getKeyId()

    def getPublicKey(self):
        """
        Get the keyId used by this peer (this peer's identifier).

        This is stored in the key store.
        """
        return self.keyStore.getPublicKey()

    def set(self, hostKeyId, storagePath, storageValue):
        """
        Set a value on a host.

        @param hostKeyId: The key id for the destination host to set the
        given key.  This could be the local host, in which case the hostKey
        will be the same as this C{Peer}'s keyStore keyId.

        @param storagePath: The path to the key to set.  For instance, this
        could be something like /chat/<somekey>/inbox.

        @param storageValue: The value to set.
        """
        if hostKeyId == self.getKeyId():
            return self.storage.set(hostKeyId, storagePath, storageValue)
        return self.pool.send(hostKeyId, 'set', storagePath, storageValue)

    def get(self, hostKeyId, storagePath):
        """
        Get a value from a host.

        @param hostKeyId: The key id for the destination host to get the
        given key.  This could be the local host, in which case the hostKey
        will be the same as this C{Peer}'s keyStore keyId.

        @param storagePath: The path to the key to get.  For instance, this
        could be something like /chat/<somekey>/inbox.
        """
        if hostKeyId == self.getKeyId():
            self.log.debug("getting storagePath %s on self" % storagePath)
            return self.storage.get(hostKeyId, storagePath)
        self.log.debug("getting storagePath %s on %s" % (storagePath, hostKeyId))
        return self.pool.send(hostKeyId, 'get', storagePath)

    def push(self, hostKeyId, storagePath, storageValue):
        """
        Given key, create a new key at <key>/<id> with the given value, where <id>
        is an auto-incrementing integer value starting at 0.
        """
        if hostKeyId == self.getKeyId():
            return self.storage.push(hostKeyId, storagePath, storageValue)
        return self.pool.send(hostKeyId, 'push', storagePath, storageValue)

    def ls(self, hostKeyId, storagePath, offset, length):
        """
        Given key, get all children keys (with the given offset and length).  Length cannot
        be more than 1000.
        """
        if hostKeyId == self.getKeyId():
            return self.storage.ls(hostKeyId, storagePath, offset, length)
        return self.pool.send(hostKeyId, 'ls', storagePath, offset, length)
