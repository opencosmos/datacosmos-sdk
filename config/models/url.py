"""Module defining a structured URL configuration model.

Ensures that URLs contain required components such as protocol, host,
port, and path.
"""

from pydantic import BaseModel

from datacosmos.utils.url import URL as DomainURL


class URL(BaseModel):
    """Generic configuration model for a URL.

    This class provides attributes to store URL components and a method
    to convert them into a `DomainURL` instance.
    """

    protocol: str
    host: str
    port: int
    path: str

    def as_domain_url(self) -> DomainURL:
        """Convert the URL instance to a `DomainURL` object.

        Returns:
            DomainURL: A domain-specific URL object.
        """
        return DomainURL(
            protocol=self.protocol,
            host=self.host,
            port=self.port,
            base=self.path,
        )
