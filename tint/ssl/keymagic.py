import uuid
import time
import os
import glob
import hashlib

from OpenSSL import crypto
from twisted.internet import ssl
from twisted.application import service

from tint.log import Logger


def sha256(s):
    return hashlib.sha256(s).hexdigest()


class DuplicateIssuer(Exception):
    """
    Each issuer (aka, CA) is unique to each user.  There shouldn't
    be two authorized keys with the same issuer.
    """


class DuplicateKeyFilename(Exception):
    """
    Each key filename is unique to you.  There shouldn't
    be two authorized keys with the same filename.
    """


class InvalidIssuer(Exception):
    """
    If an cert issuer can't be found in the local authorized keys,
    this should be raised.
    """


class InvalidAuthorizedKeyFilename(Exception):
    """
    If the key filename is not comprised of one or more alpha numeric
    characters, this should be raised.
    """


class PublicKey(object):
    def __init__(self, pemContents):
        self.pemContents = pemContents
        self.cert = ssl.Certificate.loadPEM(pemContents)

    def getIssuer(self):
        return self.cert.getIssuer().commonName

    @classmethod
    def load(Class, path):
        with open(path, 'r') as f:
            contents = f.read()
        return Class(contents)

    def store(self, path):
        with open(path, 'w') as f:
            f.write(self.pemContents)

    def getKeyId(self):
        return sha256(self.pemContents)

    def __str__(self):
        return self.pemContents


class KeyPair(object):
    def __init__(self, pemContents):
        self.pemContents = pemContents
        self.kp = ssl.PrivateCertificate.loadPEM(pemContents)

    def getKeyId(self):
        return self.getPublicKey().getKeyId()

    def getPublicKey(self):
        return PublicKey(self.kp.dump(crypto.FILETYPE_PEM))

    def generateSignedTmpKeyPair(self, expiresIn):
        # make a copy of subject, with different common name
        dn = self.kp.getSubject()
        dn.commonName = "%s-tmp" % self.kp.getIssuer().commonName

        privkey = ssl.KeyPair.generate(crypto.TYPE_RSA, size=1024)
        cert = self.kp.privateKey.signRequestObject(
            self.kp.getIssuer(),
            privkey.requestObject(dn, 'sha1'),
            int(time.time()),
            expiresIn,
            digestAlgorithm='sha1')
        return (privkey, cert)

    @classmethod
    def generate(Class):
        kp = ssl.KeyPair.generate(crypto.TYPE_RSA, size=2048)
        # a unique id for this key's common name - used as issuer
        # for all subsequent signed keys
        commonName = str(uuid.uuid4())
        signed = kp.selfSignedCert(int(time.time()), commonName=commonName)
        return Class(signed.dumpPEM())

    @classmethod
    def load(Class, path):
        with open(path, 'r') as f:
            contents = f.read()
        return Class(contents)

    def store(self, path):
        with open(path, 'w') as f:
            f.write(self.kp.dumpPEM())

    def __str__(self):
        return self.pemContents


class KeyStore(service.Service):
    def __init__(self, keyPath, authorizedKeysDir):
        """
        Handle all key interactions.

        @param keyPath: Path to the key to use as this server's id. If
        it doesn't exist, it will be created.

        @param authorizedKeysDir: Path to a directory to read/write
        authorized keys to.  They are stored in memory in the keystore
        upon this object's construction.
        """
        self.log = Logger(system=self)

        # first, check our key
        if not os.path.isfile(keyPath):
            self.log.debug("%s doesn't exist; creating new keypair" % keyPath)
            self.kpair = KeyPair.generate()
            self.kpair.store(keyPath)
        else:
            self.log.debug("using %s as this node's keypair" % keyPath)
            self.kpair = KeyPair.load(keyPath)

        # load other keys
        self.authorizedKeysDir = authorizedKeysDir
        self.refreshAuthorizedKeys()

    def startService(self):
        self.log.debug("Using keypair id: %s" % self.getKeyId())
        service.Service.startService(self)

    def getKeyId(self):
        return self.kpair.getKeyId()

    def getPublicKey(self):
        return self.kpair.getPublicKey()

    def generateSignedTmpKeyPair(self, expiresIn):
        self.log.debug("Creating a new tmp keypair that expires in %i seconds" % expiresIn)
        return self.kpair.generateSignedTmpKeyPair(expiresIn)

    def refreshAuthorizedKeys(self):
        self.authorizedKeys = {}
        pemFilter = os.path.join(self.authorizedKeysDir, "*.pem")
        for fname in glob.glob(pemFilter):
            self.log.debug("Loading %s into authorized keys" % fname)
            keyId = PublicKey.load(fname).getIssuer()
            if keyId in self.authorizedKeys:
                msg = "There are two keys with the same issuer - %s and %s."
                msg += "  Only one can be used - please delete the duplicate."
                raise DuplicateIssuer(msg % (fname, self.authorizedKeys[keyId]))
            self.authorizedKeys[keyId] = fname

    def getIssuerPublicKey(self, issuerCommonName):
        # this shouldn't happen - if a connection is successfully made,
        # then that means the key *must* be in the local authorized keys.
        # However, this is a double check, cause safety first and all that.
        if issuerCommonName not in self.authorizedKeys:
            msg = "Issuer %s could not be found in local authorized keys"
            raise InvalidIssuer(msg % issuerCommonName)
        return PublicKey.load(self.authorizedKeys[issuerCommonName])

    def getAuthorizedKeysList(self):
        return [PublicKey.load(fname) for fname in self]

    def setAuthorizedKey(self, publicKey, fname):

        path = os.path.join(self.authorizedKeysDir, fname + ".pem")

        if not fname.isalnum():
            msg = "Filename %s is not alpha numeric"
            raise InvalidAuthorizedKeyFilename(msg % fname)

        if path in self:
            msg = "There is already a key with the same filename - %s."
            msg += "  If you want to update - please delete first."
            raise DuplicateKeyFilename(msg % fname)

        if publicKey.getIssuer() in self.authorizedKeys:
            msg = "There are two keys with the same issuer - %s and %s."
            msg += "  Only one can be used - please delete the duplicate."
            raise DuplicateIssuer(msg % (fname, self.authorizedKeys[publicKey.getIssuer()]))

        publicKey.store(path)
        self.refreshAuthorizedKeys()

    def __len__(self):
        return len(self.authorizedKeys)

    def __iter__(self):
        return self.authorizedKeys.itervalues()
