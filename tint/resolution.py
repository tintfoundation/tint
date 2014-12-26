import socket
import os

from twisted.internet import defer

from kademlia.network import Server


class DHTResolver(object):
    def __init__(self, config, bootstrapNeighbors):
        self.config = config
        if os.path.isfile(config['dht.state.cache']):
            self.kserver = Server.loadState(config['dht.state.cache'])
        else:
            self.kserver = Server()
            self.kserver.bootstrap(bootstrapNeighbors)
        self.kserver.saveStateRegularly(config['dht.state.cache'], 60)

    def getProtocol(self):
        return self.kserver.protocol

    def getPublicKey(self, keyId):
        """
        Get the public key from the network, and return only if the key is
        the one that matches the keyId based on hash.
        """
        def verify(key):
            if key is not None and PublicKey(key).getKeyId() == keyId:
                return key
            return None
        return self.kserver.get(keyId).addCallback(verify)

    def resolve(self, keyId):
        return self.kserver.get("%s-location" % keyId)

    def announceLocation(self, myKeyId, myPublicKey):
        def announce(ips):
            ips = [self.localAddress()] + ips
            ipports = map(lambda ip: "%s:%i" % (ip, self.config['s2s.port']), ips)
            return self.kserver.set("%s-location" % myKeyId, ",".join(ipports))
        d = self.kserver.set(myKeyId, str(myPublicKey))
        d.addCallback(lambda _: self.kserver.inetVisibleIP())
        return d.addCallback(announce)

    def localAddress(self):
        return socket.gethostbyname(socket.gethostname())
