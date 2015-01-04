import anydbm

from itertools import imap

from zope.interface import implements
from zope.interface import Interface

from twisted.internet import defer

from tint.storage.permissions import PermissionedStorage
from tint.storage.addressing import Path
from tint.log import Logger


class IStorage(Interface):
    """
    Storage that should be durable and acidic.
    """
    def get(key, default=None):
        """
        Get a key.  Optional default if not found can be returned.
        """

    def set(key, value):
        """
        Set a key with the given value.
        """

    def push(key, value):
        """
        Given key, create a new key at <key>/<id> with the given value, where <id>
        is an auto-incrementing integer value.
        """

    def ls(key, offset=0, length=100):
        """
        Return a list of child keys at the given location, starting with the given offset
        and for the given length.  Length cannot be more than 1000.
        """


class AnyDBMStorage(object):
    implements(IStorage)

    def __init__(self, filename):
        self.filename = filename
        self.log = Logger(system=self)
        self.db = anydbm.open(self.filename, 'c')

    def get(self, key, default=None):
        self.log.debug("Getting %s" % key)
        value = self.db[key] if key in self.db else default
        return defer.succeed(value)

    def set(self, key, value):
        self.log.debug("Setting %s = %s" % (key, value))
        self.db[key] = str(value)
        return defer.succeed(self.db[key])

    def push(self, key, value):
        def dopush(current):
            id = int(current) + 1
            vkey = path.join(id).path
            d = defer.gatherResults([self.set(mkey, id), self.set(vkey, value)])
            return d.addCallback(lambda _: vkey)
        path = Path(key)
        mkey = path.join('_maxid').path
        return self.get(mkey, '-1').addCallback(dopush)

    def ls(self, key, offset=0, length=100):
        length = min(length, 1000)
        kids = set([])
        path = Path(key)
        for k in imap(Path, self.db.keys()):
            if k in path:
                kids.add(path.childFrom(k))
        kids = [ str(kid) for kid in kids if kid != '_maxid' ]
        kids.sort()
        results = []
        for k in kids[offset:][:length]:
            results.append({ 'key': k, 'value': self.db[path.join(k).path] })
        return defer.succeed(results)


class PermissionedAnyDBMStorage(PermissionedStorage):
    def __init__(self, filename):
        PermissionedStorage.__init__(self, AnyDBMStorage(filename))
