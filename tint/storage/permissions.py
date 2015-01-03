from tint.log import Logger


class NotAuthorizedError(Exception):
    """
    Someone is trying to access something they can't.
    """


class DefaultPermissions(object):
    def __init__(self, storage):
        self.storage = storage
        self.log = Logger(system=self)

    def accessAvailable(self, requestor, key):
        self.log.info("Testing access for %s to %s" % (requestor, key))
        access = set()
        parts = [""] + key[1:].split('/')
        while len(parts) > 0:
            path = "a/%s%s" % (requestor, "/".join(parts))
            s = self.storage.get(path, None)
            if s is not None:
                access.update(s.split(','))
            parts.pop()
        return list(access)

    def canAccess(self, requestor, key, optype='*'):
        """
        @param key The path to the storage.  Should always start with a '/'.
        """
        access = self.accessAvailable(requestor, key)
        return '*' in access or optype in access

    def grantAccess(self, requestor, key, optype="*"):
        if not self.canAccess(requestor, key, optype):
            path = "a/%s%s" % (requestor, key)
            self.storage.set(path, optype)


class PermissionedStorage(object):
    def __init__(self, storage, permissions=None):
        self.storage = storage
        self.permissions = permissions or DefaultPermissions(self.storage)

    def grantAccess(self, requestor, key, optype="*"):
        self.permissions.grantAccess(requestor, key, optype)

    def grantAllAccess(self, requestor):
        self.permissions.grantAccess(requestor, "/")

    def canAccess(self, requestor, key):
        return self.permissions.canAccess(requestor, key)

    def accessAvailable(self, requestor, key):
        return self.permissions.accessAvailable(requestor, key)

    def testAccess(self, requestor, key):
        """
        Like canAccess, except throw a NotAuthorizedError if requestor
        cannot access.
        """
        if not self.canAccess(requestor, key):
            raise NotAuthorizedError("%s cannot access %s" % (requestor, key))

    def get(self, requestor, key, default=None):
        self.testAccess(requestor, key)
        return self.storage.get(key, default)

    def set(self, requestor, key, value):
        self.testAccess(requestor, key)
        self.storage.set(key, value)

    def push(self, requestor, key, value):
        self.testAccess(requestor, key)
        self.storage.push(key, value)

    def ls(self, requestor, key, offset, length):
        self.testAccess(requestor, key)
        self.storage.ls(key, offset, length)
