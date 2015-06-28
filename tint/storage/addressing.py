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
        self.path = Path("/" + parts[1])

    def __str__(self):
        return "tint://%s%s" % (self.host, self.path)


class Path(object):
    def __init__(self, path='/'):
        self.path = Path.normalize(path)

    def ancestors(self):
        result = [Path()]
        if self == Path('/'):
            return result
        for kid in str(self)[1:].split('/'):
            result.append(result[-1].join(kid))
        return result

    def join(self, additional):
        if isinstance(additional, list):
            return reduce(lambda p, i: p.join(i), additional, Path())
        additional = str(additional)
        if additional[0] == '/':
            additional = additional[1:]
        if str(self) == "/":
            return Path("/%s" % additional)
        return Path("%s/%s" % (self, additional))

    def __eq__(self, other):
        return str(self) == str(other)

    def childFrom(self, other):
        """
        Get the immediate child component from other.  For instance,
        if this path is /one/two and the other is /one/two/three/four,
        then the immediate child component for this path is 'three'.

        Return None if this path doesn't contain the other.
        """
        if other not in self:
            return None
        start = len(self) + 1
        relative = str(other)[start:]
        return relative.split('/', 1)[0]

    def __str__(self):
        return self.path

    def __len__(self):
        return len(str(self))

    def __contains__(self, other):
        """
        Does this path contain the given one.  For instance,
        /one/two contains /one/two/three and /one/two/three/four
        (think of it as a directory containing another).
        """
        sother = str(other)
        sself = str(self)
        return sother != sself and sother.startswith(sself)

    @classmethod
    def normalize(klass, path):
        if path == '':
            path = '/'
        if path[0] != '/':
            path = "/%s" % path
        if len(path) > 1 and path[-1] == '/':
            path = path[:-1]
        return path
