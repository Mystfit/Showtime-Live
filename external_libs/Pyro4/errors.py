"""
Definition of the various exceptions that are used in Pyro.

Pyro - Python Remote Objects.  Copyright by Irmen de Jong (irmen@razorvine.net).
"""


class PyroError(Exception):
    """Generic base of all Pyro-specific errors."""
    pass


class CommunicationError(PyroError):
    """Base class for the errors related to network communication problems."""
    pass


class ConnectionClosedError(CommunicationError):
    """The connection was unexpectedly closed."""
    pass


class TimeoutError(CommunicationError):
    """
    A call could not be completed within the set timeout period,
    or the network caused a timeout.
    """
    pass


class ProtocolError(CommunicationError):
    """Pyro received a message that didn't match the active Pyro network protocol, or there was a protocol related error."""
    pass


class MessageTooLargeError(ProtocolError):
    """Pyro received a message or was trying to send a message that exceeds the maximum message size as configured."""
    pass


class NamingError(PyroError):
    """There was a problem related to the name server or object names."""
    pass


class DaemonError(PyroError):
    """The Daemon encountered a problem."""
    pass


class SecurityError(PyroError):
    """A security related error occurred."""
    pass


class SerializeError(ProtocolError):
    """Something went wrong while (de)serializing data."""
    pass
