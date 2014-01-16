import os

from kademlia.network import Server


class DHTResolver(object):
    def __init__(self, config, bootstrapNeighbors):
        if os.path.isfile(config['dht.state.cache']):
            self.kserver = Server.load(config['dht.state.cache'])
        else:
            self.kserver = Server()
            self.kserver.bootstrap(bootstrapNeighbors)
            self.kserver.saveRegularly(config['dht.state.cache'], 60)

    def getProtocol(self):
        return self.kserver.protocol

    def resolve(self, keyId):
        return self.kserver.get(keyId)
