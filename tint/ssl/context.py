import time
from OpenSSL import SSL
from twisted.internet.ssl import DefaultOpenSSLContextFactory

from tint.log import Logger


class PFSContextFactory(DefaultOpenSSLContextFactory):
    """
    Perfect forward secrecy!  I think...
    """

    def __init__(self, keyStore, expiresIn=86400):
        self.keyStore = keyStore
        self.expiresIn = expiresIn
        self.expiresAt = time.time() + self.expiresIn
        # we cache this so we can check for changes
        self.keyStoreSize = len(self.keyStore)
        self._context = self._makeContext()
        self.log = Logger(system=self)

    def verifyCallback(self, connection, x509, errnum, errdepth, ok):
        print "verifying cert: ", x509.get_subject()
        if not ok:
            self.log.error("invalid cert from subject: %s" % x509.get_subject())
            return False
        return True

    def getContext(self):
        if self.expiresAt <= time.time() or len(self.keyStore) != self.keyStoreSize:
            msg = "asking keystore for new temporary keypair exipiring in %i seconds"
            self.log.debug(msg % self.expiresIn)
            self._context = self._makeContext()
            self.expiresAt = time.time() + self.expiresIn
            self.keyStoreSize = len(self.keyStore)
        return self._context

    def _makeContext(self):
        privkey, signedcert = self.keyStore.generateSignedTmpKeyPair(self.expiresIn)
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.set_options(SSL.OP_NO_SSLv2)
        context.use_privatekey(privkey.original)
        context.use_certificate(signedcert.original)
        flags = SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT
        context.set_verify(flags, self.verifyCallback)
        for fpath in self.keyStore:
            context.load_verify_locations(fpath)
        return context
