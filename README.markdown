# Tint
Tint is an experimental communications network that enables [friend-to-friend (F2F)](http://en.wikipedia.org/wiki/Friend-to-friend) communication via a simple protocol.

Here are the goals:
 1. Provide a secure method for communication between trusted peers (i.e., friends) without reliance on any intermediaries or single points of failure.
 1. Provide the tools necessary to create applications that run in a browser that take advantage of being able to securely communicate with peers.
 1. Provide a simple storage mechanism that enables local addressible storage and replication without having to rely on peers to retrieve content.

Here are the basic properties:
 * All users are identified via a sha256 hash of a public key
 * The mapping of sha256 to public key are stored in a [distributed hash table](http://en.wikipedia.org/wiki/Distributed_hash_table)
 * The DHT also contains a mapping of sha256 ids to location on the internet (ip, port)
 * Friends can connect by looking up each other's identities in the DHT and then creating a TCP connection.  Peer authentication is based on server/client key based authentication.
 * Each host (aka, "hub") provides a set of RPC commands to authenticated peers (in addition to running a DHT server).
 * The RPC commands are also exposed via an HTTP interface, allowing front-end (Javascript) applications to interact with the hub.  This allows for easy application development since it can all occur in a browser.

# Running a Hub
A hub is just the bundled collection of the HTTPS, RPC, and DHT services.  There is a single keypair/identity tied to each hub representing a single user (though this may change in the future so that some number of trusted users can utilize the same hub).  A hub can be either local (aka, running on a user's local machine) or remote (aka, running on a server or a [Raspberry Pi](http://www.raspberrypi.org/)).

The following sections list the basic process for running a hub in either configuration.  Many details will be filled in later.

### Local Hub
The basic process for running a local hub is simple:
* Download software and start the service.
* Ensure that port 8468 (i.e., TINT on a number pad) is open and internet visible
* Visit http://127.0.0.1 and follow the instructions on sharing your identity with friends and adding your friends identities


### Remote Hub (preferred)
In this scenario, an internet visible machine will be running as a hub.  Assuming this is a preconfigured Rasberry Pi, you would:
* Plug in your Pi between your router and your modem
* Plug in the thumbdrive you received with your Pi and install the chrome extension and public key to their local machine's keystore (to prevent invalid cert errors in the browser)
* Click connect on the button in chrome and follow the instructions on sharing your identity with friends and adding your friends identities


# Protocols
Each hub will run a number of services:
* DHT - this is based on [Kademlia](http://en.wikipedia.org/wiki/Kademlia)
* RPC - this is a simple line-based protocol like memcache that is via SSL and mutual key-based authentication
* HTTPS - this provides an interface for front end clients to access the hub and applications that may be running there.

### DHT
Uses the [kademlia library](https://github.com/bmuller/kademlia).

### RPC
The RPC protocol is extremely simple and is used solely to provide an interface to a datastore hosted on the hub.  There are three methods:

* **get(key)**: Get the value of a key.  If the key doesn't exist, return null.
* **set(key, value)**: Set the value of a key.
* **incr(key, amount, initial)**: Increment the counter at the given key by the given amount.  Use the given initial value if no value was set.

Each key is treated as a */* separated path to a specific item.  Permissions are path based (for instance, if another user has access to the key "/AnApplication/top" then the user also has access to all descendant paths like "/AnApplication/top/something/blah".  Access to "/" means access to all storage.  Permissions are controlled either through the command line on the hub or via the web interface.

### HTTP(S)
The web interface allows the hub owner to control permissions and install/access applications.  There are really two interfaces - one is HTTPS and runs on all network interfaces, the others HTTP and runs only on the local interface (127.0.0.1).  To access the HTTPS interface, you will need to install the root certificate created by the hub so that you don't get certificate validity errors in the browser (and so that no one can impersonate the hub).

The HTTPS interface does two things:
* It hosts static pages that are each single-page Javascript applications.  One of these is an admin application that allows users to install other applications, add keys for trusted peers, and control permissions for those authorized peers.
* It provides an AJAX interface for the single-page Javascript applications (allowing them to access storage, set permissions, and add applications).

The AJAX interface has three major sections - storage, keys, and apps.  All parameters should be form encoded.  The root path is:

    http://host/api/v1

#### Storage
You can get/set/incr storage just like the RPC methods (accessing data both on the user's hub as well as the hubs of any connected friends).

Keys look like:

     tint://destsha/appname/something/something

To GET a key, use the root path followed by the key without the protocol.  For instance, send an HTTP GET to:

   http://*host*/api/v1/storage/*dest sha*/chat/*my sha*/inbox

to get the value for */chat/my sha/inbox* on the host identified by *dest sha*.

To set the value, send a POST to the same URL structure with a *data* parameter set to the thing you want to save.  To send an increment, use a PUT with optional parameters of amount (could be negative to make a decrement) and default (what to start with if there isn't a value).  An increment will return the current value.

#### Keys
Use a GET to the path:

    http://*host*/api/v1/keys

To get a JSON output of the current host key and a list of all trusted keys.

Eventually, you'll be able to POST a new key or a new hash (and then the public key will be looked up on the DHT).  For now, you can manually add keys by placing them in the *keys/authorized* folder.

#### Applications
Add should post the actual HTML (or the URL of) an app.

* Path: /api/v1/apps
* Methods: add, delete

# Why Not Just Use X
First and foremost issue: None of the alternatives below make it easy to build applications that use the system/protocol.  With Tint, an application can be a few lines of Javascript.  Secondly, they **all** require that bandwith (and sometimes system storage) be shared, requiring the additional complexity of resource usage/behavior monitoring.  Tint is directly friend to friend - and while that means it can be trivial to show that a connection was made - the connection is as fast as possible and doesn't rely on the resources of other users.

* [Freenet](http://en.wikipedia.org/wiki/Freenet): Data is stored in a distributed fashion (not bad, but different).  Tint stores your data on your node.
* [Gnunet](http://en.wikipedia.org/wiki/GNUnet): All peers act as routers, requiring that resources must be shared.  It's complicated to build applications that use the protocol (try to find even a simple chat application that uses gnunet).
* [Tor](http://en.wikipedia.org/wiki/Tor_\(anonymity_network\)): Doesn't enable F2F communication or storage (and it's crazy slow).
* [Pirate Bay](http://torrentfreak.com/how-the-pirate-bay-plans-to-beat-censorship-for-good-140105/): Suited for general/public distribution of content rather than F2F
* [I2P](http://en.wikipedia.org/wiki/I2P): It doesn't provide storage functionality (and has been in beta since 2003).
* [Pond](https://pond.imperialviolet.org/): Forward secure asynchronous messaging (via TOR). Per message on site, should not be used yet.
* [Bitmessage](https://bitmessage.org/wiki/Main_Page): all messages necessarily broadcast to entire network, with resulting proof of work.  High latency.

# Help
File a ticket on [Github](https://github.com/bmuller/tint) or reach out to [bmuller](https://github.com/bmuller).
