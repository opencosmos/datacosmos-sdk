"""A library for interacting with DataCosmos from Python code."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("datacosmos")
except PackageNotFoundError:
    __version__ = "unknown"
