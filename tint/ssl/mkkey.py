from twisted.internet.ssl import *
from OpenSSL import crypto

kp = KeyPair.generate(crypto.TYPE_RSA, size=2048)
private = kp.selfSignedCert(1, commonName='brian')
print private.dumpPEM()


