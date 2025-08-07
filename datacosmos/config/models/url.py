"""Structured URL configuration model for the Datacosmos SDK.

The model accepts *either* a mapping of fields
(protocol, host, port, path) **or** a raw URL string such as
``"https://example.com/api/v1"`` and converts it into a fully featured
:class:`datacosmos.utils.url.URL` instance via :py:meth:`as_domain_url`.
"""

from urllib.parse import urlparse

from pydantic import BaseModel, model_validator

from datacosmos.utils.url import URL as DomainURL


class URL(BaseModel):
    """Generic configuration model for a URL."""

    protocol: str
    host: str
    port: int
    path: str

    @model_validator(mode="before")
    @classmethod
    def _coerce_from_string(cls, data):
        """Convert a raw URL string into the dict expected by the model."""
        if isinstance(data, cls):
            return data

        if isinstance(data, str):
            parts = urlparse(data)
            if not parts.scheme or not parts.hostname:
                raise ValueError(f"'{data}' is not a valid absolute URL")

            default_port = 443 if parts.scheme == "https" else 80

            return {
                "protocol": parts.scheme,
                "host": parts.hostname,
                "port": parts.port or default_port,
                "path": parts.path.rstrip("/"),
            }

        return data

    def as_domain_url(self) -> DomainURL:
        """Convert this Pydantic model to the utility `DomainURL` object."""
        return DomainURL(
            protocol=self.protocol,
            host=self.host,
            port=self.port,
            base=self.path,
        )
