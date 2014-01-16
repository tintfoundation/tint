from OpenSSL import SSL
from twisted.python import log
import sys
from twisted.internet import ssl, reactor
from twisted.internet.protocol import Factory, Protocol

log.startLogging(sys.stdout)

from context import PFSContextFactory

class Echo(Protocol):
    def dataReceived(self, data):
        print "Got some data: ", data
        self.transport.write(data)

factory = Factory()
factory.protocol = Echo
ctx = PFSContextFactory("kia.pem", "brian.pem")
reactor.listenSSL(8000, factory, ctx)
reactor.run()





from twisted.protocols.basic import LineReceiver
from twisted.protocols.policies import TimeoutMixin

class TintProtocol(LineReceiver, TimeoutMixin):
    def __init__(self, timeOut=60):
        
