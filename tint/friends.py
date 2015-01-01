from collections import namedtuple
from twisted.internet import defer

from tint.ssl.keymagic import PublicKey
from tint.log import Logger
from tint.resolution import KeyNotResolvedError
from tint.storage.addressing import Path


Friend = namedtuple('Friend', ['id', 'name', 'key'])


class FriendsList(object):
    def __init__(self, keyStore, resolver):
        self.keyStore = keyStore
        self.resolver = resolver
        self.log = Logger(system=self)

    def addFriendById(self, name, keyId):
        """
        Lookup a public key with the given keyId and save if found.
        """
        d = self.resolver.getPublicKey(keyId)
        return d.addCallback(self._addFriendById, name)

    def _addFriendById(self, keyvalue, name):
        if keyvalue is None:
            raise KeyNotResolvedError("Could not find key for %s" % name)
        return self.addFriend(keyvalue, name)

    def addFriend(self, publicKey, name):
        """
        Add a friend with the given public key.
        """
        self.log.debug("Adding key belonging to %s: %s" % (name, publicKey))
        pk = PublicKey(publicKey)
        path = str(Path(pk.getKeyId()))
        self.storage.grantAccess(pk.getKeyId(), path)
        self.keyStore.setAuthorizedKey(pk, name)
        f = Friend(pk.getKeyId(), name, publicKey)
        return defer.succeed(f)

    def removeFriend(self, name):
        return self.keyStore.removeAuthorizedKey(name)

    def getFriends(self):
        friends = []
        for key in self.keyStore.getAuthorizedKeysList():
            friend = Friend(key.getKeyId(), key.name, str(key))
            friends.append(friend)
        return friends

    def __iter__(self):
        for friend in self.getFriends():
            yield friend

    def __len__(self):
        return len(self.getFriends())
