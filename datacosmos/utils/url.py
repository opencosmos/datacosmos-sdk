"""URL utility class for building and handling URLs in the SDK."""


class URL:
    """Class to represent and build URLs in a convenient way."""

    def __init__(self, protocol: str, host: str, port: int, base: str):
        """Creates a new basis to build URLs.

        Args:
            protocol (str): Protocol to use in the URL (http/https).
            host (str): Hostname (e.g., example.com).
            port (int): Port number.
            base (str): Base path (e.g., /api/v1).
        """
        self.protocol = protocol
        self.host = host
        self.port = port
        self.base = base

    def string(self) -> str:
        """Returns the full URL as a string."""
        port = "" if self.port in [80, 443] else f":{self.port}"
        base = f"/{self.base.lstrip('/')}" if self.base else ""
        return f"{self.protocol}://{self.host}{port}{base}"

    def with_suffix(self, suffix: str) -> str:
        """Appends a suffix to the URL, ensuring proper formatting.

        Args:
            suffix (str): The path to append.

        Returns:
            str: Full URL with the suffix.
        """
        base = self.string()
        return f"{base.rstrip('/')}/{suffix.lstrip('/')}"
