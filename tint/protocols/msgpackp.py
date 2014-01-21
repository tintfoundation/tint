from collections import deque

from twisted.protocols.policies import TimeoutMixin
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred, TimeoutError, maybeDeferred

import umsgpack


class NoSuchCommand(Exception):
    """
    Exception raised when a non existent command is called.
    """


class Command(object):
    def __init__(self, command, args):
        self.command = command
        self.args = args
        self._deferred = Deferred()

    def encode(self):
        c = [self.command] + list(self.args)
        return umsgpack.packb(c)

    @classmethod
    def decode(self, data):
        parts = umsgpack.unpackb(data)
        return Command(parts[0], parts[1:])

    def success(self, value):
        self._deferred.callback(value)

    def fail(self, error):
        self._deferred.errback(error)

    def __str__(self):
        args = ", ".join([str(a) for a in self.args])
        return "<Command %s(%s)>" % (self.command, args)


class MsgPackProtocol(Protocol, TimeoutMixin):
    _disconnected = False
    _buffer = ''
    _expectedLength = None

    def __init__(self, timeOut=10):
        self._current = deque()
        self.persistentTimeOut = self.timeOut = timeOut

    def _cancelCommands(self, reason):
        while self._current:
            cmd = self._current.popleft()
            cmd.fail(reason)

    def timeoutConnection(self):
        self._cancelCommands(TimeoutError("Connection timeout"))
        self.transport.loseConnection()

    def connectionLost(self, reason):
        self._disconnected = True
        self._cancelCommands(reason)
        Protocol.connectionLost(self, reason)

    def dataReceived(self, data):
        self.resetTimeout()
        self._buffer += data

        if self._expectedLength is None:
            parts = self._buffer.split(' ', 1)
            self._expectedLength = int(parts[0])
            self._buffer = parts[1]

        if len(self._buffer) >= self._expectedLength:
            data = self._buffer[1:self._expectedLength]
            self._request = self._buffer[0] == '>'
            self.commandReceived(data) if self._request else self.responseReceived(data)
            self._buffer = self._buffer[self._expectedLength:]
            self._expectedLength = None

        if len(self._buffer) > 0:
            self.dataReceived('')

    def commandReceived(self, data):
        cmdObj = Command.decode(data)
        cmd = getattr(self, "cmd_%s" % cmdObj.command, None)
        if cmd is None:
            raise NoSuchCommand("%s is not a valid command" % cmdObj.command)
        maybeDeferred(cmd, *cmdObj.args).addCallback(self.sendResult)

    def sendResult(self, result):
        result = umsgpack.packb(result)
        self.transport.write("%i <%s" % (len(result) + 1, result))

    def sendCommand(self, cmd, args):
        if not self._current:
            self.setTimeout(self.persistentTimeOut)

        cmdObj = Command(cmd, args)
        self._current.append(cmdObj)
        data = cmdObj.encode()
        self.transport.write("%i >%s" % (len(data) + 1, data))
        return cmdObj._deferred

    def responseReceived(self, data):
        unpacked = umsgpack.unpackb(data)
        self._current.popleft().success(unpacked)
