import sys
import os

from twisted.internet import reactor
from twisted.application import service, internet
from twisted.web import server
from twisted.python.log import ILogObserver

sys.path.append(os.path.dirname(__file__))
from tint.web.root import WebRoot
from tint.storage.permanent import PermissionedAnyDBMStorage
from tint.ssl.keymagic import KeyStore
from tint.resolution import DHTResolver
from tint.peer import Peer
from tint import log
from config import CONFIG


application = service.Application("tint")
application.setComponent(ILogObserver, log.FileLogObserver(sys.stdout, log.INFO).emit)

# 1. Initialize key file if it doesn't exist.
keyStore = KeyStore(CONFIG['key'], CONFIG['authorizedkeys'])
keyStore.setServiceParent(application)

# 2. Initialize local storage, granting key hash ability to access all of db.
storage = PermissionedAnyDBMStorage(CONFIG['permanent.storage'])
storage.grantAllAccess(keyStore.getKeyId())

# 3. start up DHT based on initial list, store current location and public key in DHT
resolver = DHTResolver(CONFIG, [("107.170.3.146", 8468)])
kserver = internet.UDPServer(CONFIG['dht.port'], resolver.getProtocol())
kserver.setServiceParent(application)
reactor.callLater(5, resolver.announceLocation, keyStore.getKeyId(), keyStore.getPublicKey())

# 4. Start local NodeToNode service.
peer = Peer(keyStore, storage, resolver)
pserver = internet.SSLServer(CONFIG['s2s.port'], peer.protocolFactory, peer.contextFactory)
pserver.setServiceParent(application)

# 5. Start local web interface.
web = WebRoot(peer)
server = internet.TCPServer(CONFIG['web.port'], server.Site(web), interface="127.0.0.1")
server.setServiceParent(application)
