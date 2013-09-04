"""Slick Exceptions.
Exception
    |_SlickException
"""


class SlickException(Exception):
  """Base calss for all Slick Exceptions."""
  pass


class ConnectionNotFound(SlickException):
  """Connetion to the switch/middlebox machine is lost."""
  pass


class ElementNotFound(SlickException):
  """Throw exception if invalid element instantiation is requested."""
  pass


class ApplicationNotFound(SlickException):
  """Throw this exception if invalid application name is specified."""
  pass


class InstanceNotFound(SlickException):
  """Throw exception if the application/element instance is not found."""
  pass

class ElementDownloadFailed(SlickException):
  """Throw exception if the element download is failed during placement."""
  pass
