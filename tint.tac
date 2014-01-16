"""
Startup process:

1. initialize key file if doesn't exist
2. initialize local storage, granting key hash ability to access all of db
3. start up DHT based on initial list (from where?)
4. start up local NodeToNode service
5. start up local web interface
"""
import sys
import os

from twisted.application import service, internet
from twisted.web import server

sys.path.append(os.path.dirname(__file__))
from tint.web.root import WebRoot
from tint.storage.permanent import PermissionedAnyDBMStorage
from tint.ssl.keymagic import KeyStore
from tint.resolution import DHTResolver
from config import CONFIG

# 1. initialize key file if doesn't exist
keyStore = KeyStore(CONFIG['key'], CONFIG['authorizedkeys'])

# 2. initialize local storage, granting key hash ability to access all of db
storage = PermissionedAnyDBMStorage(CONFIG['permanent.storage'])
storage.grantAllAccess(keyStore.getKeyId())

# 3. start up DHT based on initial list
application = service.Application("tint")
resolver = DHTResolver(CONFIG, [("54.193.70.32", 8468)])
server = internet.UDPServer(8468, resolver.getProtocol())
server.setServiceParent(application)

# 4. start up local NodeToNode service
# TODO

# 5. start up local web interface
web = WebRoot(storage)
server = internet.TCPServer(CONFIG['web.port'], server.Site(web))
server.setServiceParent(application)
