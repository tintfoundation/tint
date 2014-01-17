from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import Factory, ClientCreator, Protocol
from twisted.protocols.basic import LineReceiver
from twisted.protocols.policies import TimeoutMixin

from tint.protocols.msgpackp import MsgPackProtocol
from tint.ssl.context import PFSContextFactory
from tint.log import Logger


class TintProtocol(MsgPackProtocol):
    def __init__(self, connectionPool, timeout=10):
        """
        We have access to the connection pool so we can store connections
        there after they've been successfully made.
        """
        MsgPackProtocol.__init__(self, timeout)
        self.connectionPool = connectionPool
        self.log = Logger(system=self)
        self.peersKeyId = None

    def getPeersKeyId(self):
        if self.peersKeyId is None:
            issuer = self.transport.getPeerCertificate().get_issuer()
            issuerCommonName = issuer.commonName
            key = self.connectionPool.keyStore.getIssuerPublicKey(issuerCommonName)
            self.peersKeyId = key.getKeyId()
        return self.peersKeyId

    def dataReceived(self, data):
        self.connectionPool.saveConnection(self, self.getPeersKeyId())        
        self.log.debug("received data from %s: %s" % (self.getPeersKeyId(), data))
        MsgPackProtocol.dataReceived(self, data)

    def connectionLost(self, reason):
        keyId = self.getPeersKeyId()
        self.log.warning("Connection to %s lost: %s" % (keyId, str(reason)))
        self.connectionPool.forgetConnection(keyId)
        MsgPackProtocol.connectionLost(self, reason)

    def connectionFailed(self, reason):
        self.log.warning("Connection failed: %s" % str(reason))

    def cmd_get(self, key):
        return "key is %s" % key

    def cmd_set(self, key, value):
        return "setting %s = %s" % (key, value)


class TintProtocolFactory(Factory):
    protocol = TintProtocol

    def __init__(self, connectionPool):
        self.connectionPool = connectionPool
        self.log = Logger(system=self)

    def buildProtocol(self, addr):
        p = self.protocol(self.connectionPool)
        p.factory = self
        return p


class ConnectionPool(object):
    def __init__(self, resolver, contextFactory, keyStore):
        self.connections = {}
        self.resolver = resolver
        self.contextFactory = contextFactory
        self.keyStore = keyStore
        self.log = Logger(system=self)

    def send(self, keyId, cmd, *args):
        if keyId in self.connections:
            return self.sendOnConnection(self.connections[keyId], cmd)
        d = self.resolver.resolve(keyId)
        d.addCallback(self.createConnection, keyId)
        return d.addCallback(self.sendOnConnection, cmd, args)

    def sendOnConnection(self, connection, cmd, args):
        if connection is None:
            return False
        return connection.sendCommand(cmd, args)

    def createConnection(self, addr, keyId):
        if addr is None:
            return False

        host, port = addr
        cc = ClientCreator(reactor, TintProtocol, self)
        d = cc.connectSSL(host, port, self.contextFactory)
        return d.addCallback(self.saveConnection, keyId)

    def forgetConnection(self, keyId):
        self.log.info("removing connection %s from pool" % keyId)
        del self.connections[keyId]

    def saveConnection(self, connection, keyId):
        self.connections[keyId] = connection
        self.log.info("saving connection %s in pool" % keyId)
        return connection
