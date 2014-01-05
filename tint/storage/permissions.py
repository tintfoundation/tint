class DefaultPermissions(object):
    def __init__(self, storage):
        self.storage = storage

    def canAccess(self, requestor, key):
        parts = key.split('/')
        while len(parts) > 0:
            path = "a/%s/%s" % (requestor, "/".join(parts))
            if self.storage.get(path, None) == '1':
                return True
            parts.pop()
        return False

    def grantAccess(self, requestor, key):
        if not self.canAccess(requestor, key):
            path = "a/%s/%s" % (requestor, key)
            self.storage.set(path, '1')


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

    def incr(self, key, amount=1, default=0):
        self.testAccess(requestor, key)
        self.storage.incr(key, amount, default)
