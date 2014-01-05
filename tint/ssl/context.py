import time
from OpenSSL import crypto
from OpenSSL import SSL

from twisted.internet.ssl import DefaultOpenSSLContextFactory
from twisted.internet.ssl import KeyPair
from twisted.internet.ssl import PrivateCertificate
from twisted.internet.ssl import DistinguishedName
from twisted.internet.ssl import Certificate

from twisted.python import log

class PFSContextFactory(DefaultOpenSSLContextFactory):
    """
    Perfect forward secrecy!  I think...
    """

    _context = None
    
    def __init__(self, localCAFileName, remoteCAFileName, expiresIn=86400):
        with open(localCAFileName, 'r') as capem:
            self.caroot = PrivateCertificate.loadPEM(capem.read())
        self.dn = self.caroot.getSubject()
        self.dn.commonName = self.caroot.getPublicKey().keyHash()
        self.expiresIn = expiresIn
        self.remoteCAFileName = remoteCAFileName

    def verifyCallback(self, connection, x509, errnum, errdepth, ok):
        if not ok:
            log.err("invalid cert from subject: %s" % x509.get_subject())
            return False
        else:
            return True

    def getContext(self):
        if self._context is not None:
            return self._context

        privkey = KeyPair.generate(crypto.TYPE_RSA, size=1024)
        signedcert = self.caroot.privateKey.signRequestObject(
            self.caroot.getIssuer(),
            privkey.requestObject(self.dn, 'sha1'),
            int(time.time()),
            self.expiresIn,
            digestAlgorithm='sha1')

        self._context = SSL.Context(SSL.SSLv23_METHOD)
        self._context.set_options(SSL.OP_NO_SSLv2)
        self._context.use_privatekey(privkey.original)
        self._context.use_certificate(signedcert.original)
        flags = SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT
        self._context.set_verify(flags, self.verifyCallback)
        self._context.load_verify_locations(self.remoteCAFileName)            
        return self._context
