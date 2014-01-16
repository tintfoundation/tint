from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import Factory, ClientCreator, Protocol
from twisted.protocols.basic import LineReceiver
from twisted.protocols.policies import TimeoutMixin

from tint.ssl.context import PFSContextFactory
from tint.log import Logger


class TintProtocol(LineReceiver):
    def __init__(self, connectionPool):
        """
        We have access to the connection pool so we can store connections
        there after they've been successfully made.
        """
        self.connectionPool = connectionPool

    def cacheConnection(self):
        peer = self.transport.getPeer()
        print "connection made from ", self.transport.getPeerCertificate()
        if not self.connectionPool.hasConnection(peer.host, peer.port):
            self.connectionPool.addConnection(peer.host, peer.port, self)

    def getPeersKey(self):
        issuerCommonName = self.transport.getPeerCertificate().get_issuer().commonName
        return self.factory.keyStore.getIssuerPublicKey(issuerCommonName)
        
    def lineReceived(self, line):
        self.cacheConnection()
        print "got line: ", line
        if line == "syn":
            self.sendLine("ack")

    def send(self, cmd):
        print "sending line:", cmd
        self.sendLine(cmd)


class TintProtocolFactory(Factory):
    protocol = TintProtocol

    def __init__(self, keyStore, connectionPool):
        self.keyStore = keyStore
        self.connectionPool = connectionPool
        self.log = Logger(system=self)

    def buildProtocol(self, addr):
        p = self.protocol(self.connectionPool)
        p.factory = self
        return p

    def startedConnecting(self, connector):
        """
        This will only be called if this is a client factory.
        """
        self.log.debug("starting connection")

    def clientConnectionFailed(self, connector, reason):
        """
        This will only be called if this is a client factory.
        """
        self.log.error("Connection failed: " % str(reason))

    def clientConnectionLost(self, connector, reason):
        """
        This will only be called if this is a client factory.
        """
        self.log.error("Connection lost: " % str(reason))


class ConnectionPool(object):
    this should actually only map key id to transport
    
    def __init__(self):
        self.connections = {}

    def addConnection(self, host, port, connection):
        if self.hasConnection(host, port):
            print "already have connection to %s:%i" % (host, port)
        key = "%s:%i" % (host, port)
        self.connections[key] = connection

    def hasConnection(self, host, port):
        key = "%s:%i" % (host, port)
        return key in self.connections

    def getConnection(self, host, port):
        key = "%s:%i" % (host, port)
        return self.connections.get(key, None)


class Peer(object):

    somewhere a resolver should be passed in to go from key id to ip/port
    
    def __init__(self, keyStore):
        self.keyStore = keyStore
        self.pool = ConnectionPool()        
        self.protocolFactory = TintProtocolFactory(self.keyStore, self.pool)
        self.contextFactory = PFSContextFactory(self.keyStore)

    def listen(self, port, **kwargs):
        reactor.listenSSL(port, self.protocolFactory, self.contextFactory, **kwargs)

    def send(self, host, port, cmd):
        def cacheConnection(c):
            self.pool.addConnection(host, port, c)
            return self.send(host, port, cmd)
        
        if not self.pool.hasConnection(host, port):
            cc = ClientCreator(reactor, TintProtocol, self.pool)
            d = cc.connectSSL(host, port, self.contextFactory)
            return d.addCallback(cacheConnection)

        return self.pool.getConnection(host, port).send(cmd)
