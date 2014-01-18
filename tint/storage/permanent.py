import anydbm

from tint.storage.permissions import PermissionedStorage


class MalformedURI(Exception):
    """
    Raised when URI is malformed.
    """


class TintURI(object):
    delimiter = "/"

    def __init__(self, uri):
        self.uri = uri
        if self.uri is not None:
            self.parsePath()

    def parsePath(self):
        # path must be at least tint://<sha256>
        if len(self.uri) < 47 or self.uri[:7] != "tint://":
            raise MalformedURI("URI %s is invalid" % self.uri)
        parts = self.uri[7:].split(self.delimiter, 1)
        self.host = parts[0]
        self.path = self.delimiter + parts[1]

    def __str__(self):
        return "tint://%s%s" % (self.host, self.path)


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
        if key in self.db:
            return self.db[key]
        return default

    def set(self, key, value):
        self.db[key] = str(value)

    def incr(self, key, amount=1, default=0):
        value = int(self.get(key, default)) + amount
        self.set(key, value)

    def __getitem__(self, key):
        return self.db[key]

    def __setitem__(self, key, value):
        self.db[key] = value


class PermissionedAnyDBMStorage(PermissionedStorage):
    def __init__(self, filename):
        PermissionedStorage.__init__(self, AnyDBMStorage(filename))
