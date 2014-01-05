from twisted.internet.ssl import KeyPair, Certificate
import random
import time
from OpenSSL import crypto

from tint.ssl.utils import sha256
from tint.ssl.utils import sha1

def generateKeyPair(path):
    kp = KeyPair.generate(crypto.TYPE_RSA, size=2048)
    # some unique noise - doesn't matter much, so sha1 is fine
    commonName = sha1(str(random.getrandbits(255)))
    private = kp.selfSignedCert(int(time.time()), commonName=commonName)
    with open(path, 'w') as f:
        f.write(private.dumpPEM())
    # *THE* identifier for the key.  Make it safe.
    return sha256(private.dump(crypto.FILETYPE_PEM))

def getCertSHA(path):
    with open(path, 'r') as f:
        cert = Certificate.loadPEM(f.read())
    # *THE* identifier for the key.  Make it safe.        
    return sha256(cert.dump(crypto.FILETYPE_PEM))
