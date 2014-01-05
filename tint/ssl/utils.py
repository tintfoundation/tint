import hashlib

def sha256(s):
    return hashlib.sha256(s).hexdigest()

def sha1(s):
    return hashlib.sha1(s).hexdigest()
