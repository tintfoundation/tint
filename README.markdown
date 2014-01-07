# Tint
Tint is an experimental communications network that enables [friend-to-friend (F2F)](http://en.wikipedia.org/wiki/Friend-to-friend) communication via a simple protocol.

Here are the basic properties:
 * All users are identified via a sha256 hash of a public key
 * The mapping of sha256 to public key are stored in a [distributed hash table](http://en.wikipedia.org/wiki/Distributed_hash_table)
 * The DHT also contains a mapping of sha256 ids to location on the internet (ip, port)
 * Friends can connect by looking up each other's identities in the DHT and then creating a TCP connection.  Peer authentication is based on server/client key based authentication.
 * Each host (aka, "hub") provides a set of RPC commands to authenticated peers (in addition to running a DHT server).
 * The RPC commands are also exposed via an HTTP interface, allowing front-end (Javascript) applications to interact with the hub.  This allows for easy application development since it can all occur in a browser.

# Running a Hub
A hub is just the bundled collection of the HTTPS, RPC, and DHT services.  There is a single keypair/identity tied to each hub representing a single user.  A hub can be either local (aka, running on a user's local machine) or remote (aka, running on a server or a [Raspberry Pi](http://www.raspberrypi.org/)).

The following sections list the basic process for running a hub in either configuration.  Many details will be filled in later.

## Local Hub
The basic process for running a local hub is simple:
1. Download software and start the service.
1. Ensure that port 8468 (TINT on your phone) is open and internet visible
1. Visit http://127.0.0.1 and follow the instructions on sharing your identity with friends and adding your friends identities

## Remote Hub (preferred)
In this scenario, an internet visible machine will be running as a hub.  Assuming this is a preconfigured Rasberry Pi, you would:
1. Plug in your Pi between your router and your modem
1. Plug in the thumbdrive you received with your Pi and install the chrome extension and public key
1. Click connect on the button in chrome

# Protocols
Each hub will run a number of services:
1. DHT - this is based on [Kademlia](http://en.wikipedia.org/wiki/Kademlia)
1. RPC - this is a simple line-based protocol like memcache that is via SSL and mutual key-based authentication
1. HTTPS - this provides an interface for front end clients to access the hub and applications that may be running there.

## DHT
Uses the [kademlia library](https://github.com/bmuller/kademlia).

## RPC
The RPC protocol is extremely simple and is used solely to provide an interface to a datastore hosted on the hub.  There are three methods:

* **get(key)**: Get the value of a key.  If the key doesn't exist, return null.
* **set(key, value)**: Set the value of a key.
* **incr(key, amount, initial)**: Increment the counter at the given key by the given amount.  Use the given initial value if no value was set.

Each key is treated as a */* separated path to a specific item.  Permissions are path based (for instance, if another user has access to the key "/AnApplication/top" then the user also has access to all descendant paths like "/AnApplication/top/something/blah".  Access to "/" means access to all storage.  Permissions are controlled either through the command line on the hub or via the web interface.

## HTTP(S)
The web interface allows the hub owner to control permissions and install/access applications.  There are really two interfaces - one is HTTPS and runs on all network interfaces, the others HTTP and runs only on the local interface (127.0.0.1).  To access the HTTPS interface, you will need to install the root certificate created by the hub so that you don't get certificate validity errors in the browser (and so that no one can impersonate the hub).

The HTTPS interface does two things:
1. It hosts static pages that are each single-page Javascript applications.  One of these is an admin application that allows users to install other applications, add keys for trusted peers, and control permissions for those authorized peers.
1. It provides an AJAX interface for the single-page Javascript applications (allowing them to access storage, set permissions, and add applications).

The AJAX interface has three major sections - storage, keys, and apps.  All parameters should be form encoded and use the HTTP POST method.

### Storage
You can get/set/incr storage just like the RPC methods (accessing data both on the user's hub as well as the hubs of any connected friends).  Keys look like:
tint://sourcesha@destsha/appname/something/something

* Path: /api/v1/storage
* Methods: incr / get / set

### Keys

* Path: /api/v1/keys
* Methods: add, get (my key's current location on DHT)

### Applications
Add should post the actual HTML (or the URL of) an app.

* Path: /api/v1/apps
* Methods: add, delete

# Help
Authors will hang out on irc.freenode.net#tint