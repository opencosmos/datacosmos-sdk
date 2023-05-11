"""Contains all DataCosmos exceptions."""


class DataCosmosError(Exception):
    """Base class for all DataCosmos errors."""

    pass


class DataCosmosCredentialsError(DataCosmosError):
    """Raised when there is an error loading credentials."""

    pass


class DataCosmosRequestError(DataCosmosError):
    """Raised when there is an error making a request to the DataCosmos API."""

    pass
