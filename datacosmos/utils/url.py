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

    def with_base(self, url: str) -> str:
        """Replaces the base of the url with the base stored in the URL object. (migrates url from one base to another).

        Args:
            url (str): url to migrate to the base of the URL object

        Returns (str):
            url with the base of the URL object
        """
        split_url = url.split("/")
        if len(split_url) < 3 or url.find("://") == -1:
            raise ValueError(f"URL '{url}' does not meet the minimum requirements")
        # get the whole path
        url_path = "/".join(split_url[3:])
        # simple case, matching self.base at url
        b = self.base.lstrip("/")
        if (base_pos := url_path.find(b)) != -1:
            # remove the base from the url
            url_suffix = url_path[len(b) + base_pos :]
        else:
            url_suffix = url_path
        return self.with_suffix(url_suffix)
