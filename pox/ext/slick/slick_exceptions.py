"""Slick Exceptions."""


class SlickException(Exception):
  """Base calss for all Slick Exceptions."""
  pass


class ConnectionNotFound(SlickException):
  """Connetion to the switch/middlebox machine is lost."""
  pass


class ElementNotFound(SlickException):
  """Throw exception if the element is not found."""
  pass


class ElementInstanceNotFound(SlickException):
  """Throw exception if the element instance is not found."""
  pass
