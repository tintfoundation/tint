class NotAuthorizedError(Exception):
    """
    Someone is trying to access something they can't.
    """


class DefaultPermissions(object):
    def __init__(self, storage):
        self.storage = storage

    def canAccess(self, requestor, key, optype='*'):
        """
        @param key The path to the storage.  Should always start with a '/'.
        """
        parts = key[1:].split('/')
        while len(parts) > 0:
            path = "a/%s/%s" % (requestor, "/".join(parts))
            if optype in self.storage.get(path, '').split(','):
                return True
            parts.pop()
        return False

    def grantAccess(self, requestor, key, optype="*"):
        if not self.canAccess(requestor, key):
            path = "a/%s%s" % (requestor, key)
            self.storage.set(path, optype)


class PermissionedStorage(object):
    def __init__(self, storage, permissions=None):
        self.storage = storage
        self.permissions = permissions or DefaultPermissions(self.storage)

    def grantAccess(self, requestor, key):
        self.permissions.grantAccess(requestor, key)

    def grantAllAccess(self, requestor):
        self.permissions.grantAccess(requestor, "")

    def testAccess(self, requestor, key):
        if not self.permissions.canAccess(requestor, key):
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
