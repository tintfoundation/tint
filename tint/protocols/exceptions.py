"""
All C{Exception} classes.
"""


class HostUnreachableError(Exception):
    """
    Can't find or connect to the host.
    """


class HostAuthenticationError(Exception):
    """
    Encryption error.  Host couldn't be authenticated, or we couldn't
    be authenticated.
    """
