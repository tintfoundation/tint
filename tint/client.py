from twisted.internet import ssl, reactor
from twisted.internet.protocol import ClientFactory, Protocol

from context import PFSContextFactory

class EchoClient(Protocol):
    def connectionMade(self):
        print "hello, world"
        self.transport.write("hello, world!")

    def dataReceived(self, data):
        print "Server said:", data
        self.transport.loseConnection()

class EchoClientFactory(ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye! ", reason
        reactor.stop()

ctx = PFSContextFactory("brian.pem", "kia.pem")
factory = EchoClientFactory()
reactor.connectSSL('localhost', 8000, factory, ctx)
reactor.run()
