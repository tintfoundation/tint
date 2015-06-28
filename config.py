import socket

CONFIG = {
    'key': 'keys/id.pem',
    'authorizedkeys': 'keys/authorized',
    's2s.port': 8469,
    'dht.port': 8468,
    'web.port': 8080,
    'permanent.storage': 'tint_storage',
    'dht.bootstrap': socket.gethostbyname('dht.tintspace.org'),
    'dht.state.cache': 'kademlia.pickle',
    'apps.dir': 'apps'
    }
