"""Contains logic for loading the credentials used to authenticate with DataCosmos."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from datacosmos.const import DATACOSMOS_PRODUCTION_AUDIENCE, DATACOSMOS_TOKEN_URL
from datacosmos.errors import DataCosmosCredentialsError


@dataclass
class DataCosmosCredentials:
    """Load credentials from environment variables or file.

    DataCosmosCredentials is a dataclass that provides a simple interface for
    loading credentials from either environment variables or a file.

    To load credentials from environment variables:

    >>> from datacosmos import DataCosmosCredentials
    >>> credentials = DataCosmosCredentials.from_env()

    To load credentials from a file:

    >>> from datacosmos import DataCosmosCredentials
    >>> credentials = DataCosmosCredentials.from_file("path/to/credentials.json")

    :param client_id: Client ID
    :param client_secret: Client Secret
    :param audience: Audience URL. Defaults to the production audience URL. You
        probably don't need to change this unless you are connecting to a test
        environment.
    """

    client_id: str
    client_secret: str
    audience: str = DATACOSMOS_PRODUCTION_AUDIENCE

    @classmethod
    def from_env(cls, **kwargs) -> DataCosmosCredentials:
        """Load from environment variables DATACOSMOS_KEY_ID and DATACOSMOS_KEY_SECRET.

        :return: DataCosmosCredentials object containing client ID and secret.
        """
        client_id = os.environ.get("DATACOSMOS_KEY_ID")
        if not client_id:
            raise DataCosmosCredentialsError(
                "Trying to load client id from environment variable DATACOSMOS_KEY_ID, "
                "but it is not set."
            )
        client_secret = os.environ.get("DATACOSMOS_KEY_SECRET")
        if not client_secret:
            raise DataCosmosCredentialsError(
                "Trying to load client secret from environment variable "
                "DATACOSMOS_KEY_SECRET, but it is not set."
            )
        return cls(client_id, client_secret, **kwargs)

    @classmethod
    def from_file(cls, path: str | os.PathLike, **kwargs) -> DataCosmosCredentials:
        """Load credentials from a file.

        The file should be a JSON file with the following format:

            {
                "id": "your_client_id",
                "secret": "your_client_secret"
            }

        :param path: Path to the file containing credentials.
        :return: DataCosmosCredentials object containing client ID and secret.
        """
        if not os.path.exists(path):
            raise DataCosmosCredentialsError(
                f"Trying to load credentials from file '{path}', but it does not exist."
            )
        with open(path, "r") as f:
            contents = f.read()

        try:
            obj = json.loads(contents)
        except json.JSONDecodeError:
            raise DataCosmosCredentialsError(
                f"Trying to load credentials from file '{path}', but it is not valid "
                f"JSON. Expected a JSON object with keys 'id' and 'secret'."
            )

        client_id = obj.get("id")
        if not client_id:
            raise DataCosmosCredentialsError(
                f"Trying to load credentials from file '{path}', but it does not "
                "contain an 'id' key."
            )
        client_secret = obj.get("secret")
        if not client_secret:
            raise DataCosmosCredentialsError(
                f"Trying to load credentials from file '{path}', but it does not "
                "contain a 'secret' key."
            )

        return cls(client_id, client_secret, **kwargs)

    def authenticated_session(self) -> OAuth2Session:
        """Create a Session object that is authenticated with the DataCosmos API.

        This session object can be used to make authenticated requests to the
        DataCosmos API.

        :return: OAuth2Session object that is authenticated with DataCosmos.
        """
        client = BackendApplicationClient(self.client_id)
        session = OAuth2Session(client=client)

        session.fetch_token(
            DATACOSMOS_TOKEN_URL,
            client_secret=self.client_secret,
            audience=self.audience,
        )

        return session
