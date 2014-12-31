from twisted.internet import reactor
from twisted.internet.protocol import Factory, ClientCreator

from tint.protocols.msgpackp import MsgPackProtocol
from tint.protocols.exceptions import HostUnreachableError
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
        self.storage = self.connectionPool.storage
        self.peersKeyId = None

    def getPeersKeyId(self):
        if self.peersKeyId is None:
            cert = self.transport.getPeerCertificate()
            if cert is not None:
                issuerCommonName = cert.get_issuer().commonName
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
        return self.storage.get(self.getPeersKeyId(), key)

    def cmd_set(self, key, value):
        return self.storage.set(self.getPeersKeyId(), key, value)

    def cmd_push(self, key, value):
        return self.storage.push(self.getPeersKeyId(), key, value)

    def cmd_ls(self, key, offset, length):
        return self.storage.ls(self.getPeersKeyId(), key, offset, length)


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
    def __init__(self, resolver, contextFactory, keyStore, storage):
        self.connections = {}
        self.resolver = resolver
        self.contextFactory = contextFactory
        self.keyStore = keyStore
        self.storage = storage
        self.log = Logger(system=self)

    def send(self, keyId, cmd, *args):
        if keyId in self.connections:
            return self.sendOnConnection(self.connections[keyId], cmd, args)
        d = self.resolver.resolve(keyId)
        d.addCallback(self.createConnection, keyId)
        return d.addCallback(self.sendOnConnection, cmd, args)

    def sendOnConnection(self, connection, cmd, args):
        if connection is None:
            return False
        return connection.sendCommand(cmd, args)

    def createConnection(self, addrs, keyId):
        if len(addrs) == 0:
            raise HostUnreachableError("Cannot connect to %s" % keyId)

        host, port = addrs.pop()
        self.log.debug("Attempting to create connection to %s:%i" % (host, port))
        cc = ClientCreator(reactor, TintProtocol, self)
        d = cc.connectSSL(host, port, self.contextFactory, timeout=5)
        d.addCallback(self.saveConnection, keyId)
        if len(addrs) > 0:
            d.addErrback(lambda _: self.createConnection(addrs, keyId))
        return d

    def forgetConnection(self, keyId):
        self.log.info("removing connection %s from pool" % keyId)
        if keyId in self.connections:
            del self.connections[keyId]

    def saveConnection(self, connection, keyId):
        self.connections[keyId] = connection
        self.log.info("saving connection %s in pool" % keyId)
        return connection
