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
from tint.ssl import keymagic
from config import CONFIG

if not os.path.isfile(CONFIG['key']):
    print "Keyfile %s doesn't exist, creating" % CONFIG['key']
    ourname = keymagic.generateKeyPair(CONFIG['key'])
else:
    ourname = keymagic.getCertSHA(CONFIG['key'])

storage = PermissionedAnyDBMStorage(CONFIG['permanent.storage'])
storage.grantAllAccess(ourname)

application = service.Application("tint")
web = WebRoot(storage)
server = internet.TCPServer(CONFIG['web.port'], server.Site(web))
server.setServiceParent(application)
