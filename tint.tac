import sys
import os

from twisted.application import service, internet
from twisted.web import server

sys.path.append(os.path.dirname(__file__))
from tint.web.root import WebRoot
from tint.storage.permanent import PermissionedAnyDBMStorage
from tint.ssl.keymagic import KeyStore
from tint.resolution import DHTResolver
from tint.peer import Peer
from config import CONFIG


application = service.Application("tint")

# 1. initialize key file if doesn't exist
keyStore = KeyStore(CONFIG['key'], CONFIG['authorizedkeys'])
keyStore.setServiceParent(application)

# 2. initialize local storage, granting key hash ability to access all of db
storage = PermissionedAnyDBMStorage(CONFIG['permanent.storage'])
storage.grantAllAccess(keyStore.getKeyId())

# 3. start up DHT based on initial list
resolver = DHTResolver(CONFIG, [("54.193.70.32", 8468)])
kserver = internet.UDPServer(8468, resolver.getProtocol())
kserver.setServiceParent(application)

# 4. start up local NodeToNode service
peer = Peer(keyStore, storage, resolver)
pserver = internet.SSLServer(CONFIG['s2s.port'], peer.protocolFactory, peer.contextFactory, interface="127.0.0.1")
pserver.setServiceParent(application)

# 5. start up local web interface
web = WebRoot(peer)
server = internet.TCPServer(CONFIG['web.port'], server.Site(web))
server.setServiceParent(application)
