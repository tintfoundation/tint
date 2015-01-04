from twisted.internet import defer

from tint.log import Logger
from tint.storage.addressing import Path


class NotAuthorizedError(Exception):
    """
    Someone is trying to access something they can't.
    """


class DefaultPermissions(object):
    def __init__(self, storage):
        self.storage = storage
        self.log = Logger(system=self)

    def accessAvailable(self, requestor, key):
        def gather(results):
            access = set()
            for result in results:
                if result is not None:
                    access.update(result.split(','))
            return list(access)

        self.log.info("Testing access for %s to %s" % (requestor, key))
        ds = []
        for path in Path(key).ancestors():
            path = str(Path('a').join(requestor).join(path))
            ds.append(self.storage.get(path, None))
        return defer.gatherResults(ds).addCallback(gather)

    def canAccess(self, requestor, key, optype='*'):
        """
        @param key The path to the storage.  Should always start with a '/'.
        """
        def test(access):
            return '*' in access or optype in access
        d = self.accessAvailable(requestor, key)
        return d.addCallback(test)

    def grantAccess(self, requestor, key, optype="*"):
        def test(access):
            if not access:
                path = Path('a').join(requestor).join(Path(key))
                return self.storage.set(str(path), optype)
            return defer.succeed(optype)

        d = self.canAccess(requestor, key, optype)
        return d.addCallback(test)


class PermissionedStorage(object):
    def __init__(self, storage, permissions=None):
        self.storage = storage
        self.permissions = permissions or DefaultPermissions(self.storage)

    def grantAccess(self, requestor, key, optype="*"):
        return self.permissions.grantAccess(requestor, key, optype)

    def grantAllAccess(self, requestor):
        return self.permissions.grantAccess(requestor, "/")

    def canAccess(self, requestor, key):
        return self.permissions.canAccess(requestor, key)

    def accessAvailable(self, requestor, key):
        return self.permissions.accessAvailable(requestor, key)

    def testAccess(self, requestor, key):
        """
        Like canAccess, except throw a NotAuthorizedError if requestor
        cannot access.
        """
        def _test(can):
            if not can:
                raise NotAuthorizedError("%s cannot access %s" % (requestor, key))
        d = self.canAccess(requestor, key)
        return d.addCallback(_test)

    def get(self, requestor, key, default=None):
        d = self.testAccess(requestor, key)
        return d.addCallback(lambda _: self.storage.get(key, default))

    def set(self, requestor, key, value):
        d = self.testAccess(requestor, key)
        return d.addCallback(lambda _: self.storage.set(key, value))

    def push(self, requestor, key, value):
        d = self.testAccess(requestor, key)
        return d.addCallback(lambda _: self.storage.push(key, value))

    def ls(self, requestor, key, offset, length):
        d = self.testAccess(requestor, key)
        return d.addCallback(lambda _: self.storage.ls(key, offset, length))
