from twisted.trial import unittest

from tint.storage.permanent import TintURI
from tint.ssl.keymagic import sha256

class TintURITest(unittest.TestCase):
    def test_str(self):
        hsha = sha256('hi')
        uri = TintURI("tint://%s/a/path" % hsha)
        self.assertEqual(uri.host, hsha)
        self.assertEqual(uri.path, '/a/path')

