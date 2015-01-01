import os

import netifaces

from kademlia.network import Server

from tint.log import Logger
from tint.ssl.keymagic import PublicKey


class KeyNotResolvedError(Exception):
    """
    Couldn't resolve key in the DHT.
    """


class DHTResolver(object):
    def __init__(self, config, bootstrapNeighbors):
        self.config = config
        self.log = Logger(system=self)
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

        self.log.debug("Getting key text for key id %s" % keyId)
        return self.kserver.get(keyId).addCallback(verify)

    def resolve(self, keyId):
        def parse(locations):
            self.log.debug("Locations for %s: %s" % (keyId, locations))
            results = []
            if locations is None or locations == "":
                return results
            for location in locations.split(','):
                host, port = location.split(':')
                results.append((host, int(port)))
            return results
        d = self.kserver.get("%s-location" % keyId)
        return d.addCallback(parse)

    def announceLocation(self, myKeyId, myPublicKey):
        def announce(ips):
            ips = self.localAddresses() + ips
            ipports = map(lambda ip: "%s:%i" % (ip, self.config['s2s.port']), ips)
            return self.kserver.set("%s-location" % myKeyId, ",".join(ipports))
        d = self.kserver.set(myKeyId, str(myPublicKey))
        d.addCallback(lambda _: self.kserver.inetVisibleIP())
        return d.addCallback(announce)

    def localAddresses(self):
        result = []
        for iface in netifaces.interfaces():
            addys = netifaces.ifaddresses(iface).get(netifaces.AF_INET)
            result += [ addy['addr'] for addy in (addys or []) if addy['addr'] != '127.0.0.1' ]
        return result
