import anydbm

from collections import defaultdict
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
    def subscribe(key, type, func):
        """
        Subscribe to changes to a key or one of it's children.  The key is the one to watch,
        type is one of 'value', 'child_added', or 'child_changed'.  The func should be a function
        that accepts the key that changed and the new value.
        """

    def unsubscribe(key, type, func):
        """
        Remove an existing subscription to the changes of a key or one of it's children.
        The key is the one to watch, type is one of 'value', 'child_added', or 'child_changed',
        and the func is the func to remove as a subscriber.
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


class ObservableStorage(object):
    def __init__(self):
        self.observers = defaultdict(dict)

    def subscribe(self, key, stype, func):
        """
        Subscribe to changes to a key or one of it's children.  The key is the one to watch,
        stype is one of 'value', 'child_added', or 'child_changed'.  The func should be a function
        that accepts the key that changed and the new value.
        """
        key = Path.normalize(key)
        if stype not in self.observers[key]:
            self.observers[key][stype] = []
        self.observers[key][stype].append(func)


    def unsubscribe(self, key, type, func):
        key = Path.normalize(key)
        self.observers[key][type].remove(func)

        # clean up type if now empty
        if len(self.observers[key][type]) == 0:
            del self.observers[key][type]

        # clean up key if now empty
        if len(self.observers[key]) == 0:
            del self.observers[key]


    def publishChange(self, key, value, preexisting):
        key = Path.normalize(key)
        wrap = lambda fs: map(lambda f: defer.maybeDeferred(f, key, value), fs)
        ds = []

        if key in self.observers and 'value' in self.observers[key]:
            ds += wrap(self.observers[key]['value'])

        paths = [ path for path in self.observers.keys() if key in Path(path) ]
        for path in paths:
            if preexisting and 'child_changed' in self.observers[path]:
                ds += wrap(self.observers[path]['child_changed'])
            if not preexisting and 'child_added' in self.observers[path]:
                ds += wrap(self.observers[path]['child_added'])

        if ds:
            return defer.DeferredList(ds).addCallback(lambda _: value)
        return defer.succeed(value)


class AnyDBMStorage(ObservableStorage):
    implements(IStorage)

    def __init__(self, filename):
        self.filename = filename
        self.log = Logger(system=self)
        self.db = anydbm.open(self.filename, 'c')

    def get(self, key, default=None):
        key = Path.normalize(key)
        self.log.debug("Getting %s" % key)
        value = self.db[key] if key in self.db else default
        return defer.succeed(value)

    def set(self, key, value):
        key = Path.normalize(key)
        self.log.debug("Setting %s = %s" % (key, value))
        preexisting = key in self.db
        self.db[key] = str(value)
        return self.publishChange(key, value, preexisting)

    def push(self, key, value):
        path = Path(key)
        mkey = path.join('_maxid').path

        def dopush(current):
            id = int(current) + 1
            vkey = path.join(id).path
            d = defer.gatherResults([self.set(mkey, id), self.set(vkey, value)])
            return d.addCallback(lambda _: self.publishChange(vkey, value, False))
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
