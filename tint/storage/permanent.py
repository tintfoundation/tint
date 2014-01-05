import anydbm

from tint.storage.permissions import PermissionedStorage


class PermanentStorage(object):
    def __init__(self, filename):
        self.filename = filename

    def get(self, key, default=None):
        raise NotImplementedError

    def set(self, key, value):
        raise NotImplementedError

    def incr(self, key, amount=1, default=0):
        raise NotImplementedError


class AnyDBMStorage(PermanentStorage):
    def __init__(self, filename):
        PermanentStorage.__init__(self, filename)
        self.db = anydbm.open(self.filename, 'c')

    def get(self, key, default=None):
        if self.db.has_key(key):
            return self.db[key]
        return default

    def set(self, key, value):
        self.db[key] = str(value)

    def incr(self, key, amount=1, default=0):
        value = self.get(key, default) + amount
        self.set(key, value)

    def __getitem__(self, key):
        return self.db[key]

    def __setitem__(self, key, value):
        self.db[key] = value


class PermissionedAnyDBMStorage(PermissionedStorage):
    def __init__(self, filename):
        PermissionedStorage.__init__(self, AnyDBMStorage(filename))
