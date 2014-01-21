import os

from twisted.internet import defer

from kademlia.network import Server


class DHTResolver(object):
    def __init__(self, config, bootstrapNeighbors):
        if os.path.isfile(config['dht.state.cache']):
            self.kserver = Server.loadState(config['dht.state.cache'])
        else:
            self.kserver = Server()
            self.kserver.bootstrap(bootstrapNeighbors)
            self.kserver.saveStateRegularly(config['dht.state.cache'], 60)

    def getProtocol(self):
        return self.kserver.protocol

    def resolve(self, keyId):
        return self.kserver.get(keyId)

    def announceLocation(self, myKeyId):
        def announce(ips):
            if len(ips) == 0:
                return defer.succeed(False)
            return self.kserver.set(myKeyId, ips[0])
        d = self.kserver.inetVisibleIP()
        return d.addCallback(announce)
