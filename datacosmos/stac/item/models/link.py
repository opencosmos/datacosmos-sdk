"""Model representing a STAC 1.1.0 link object."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class Link(BaseModel):
    """Model representing a STAC 1.1.0 link object.

    Includes HTTP request metadata fields added in STAC 1.1.0.
    Spec: https://github.com/radiantearth/stac-spec/blob/master/commons/links.md
    """

    model_config = ConfigDict(extra="allow")

    href: str
    rel: str
    type: str | None = None
    title: str | None = None
    method: str | None = None
    headers: dict[str, list[str]] | None = None
    body: Any | None = None


# Link relation constants defined by the STAC specification
LINK_REL_SELF = "self"
LINK_REL_ROOT = "root"
LINK_REL_PARENT = "parent"
LINK_REL_CHILD = "child"
LINK_REL_COLLECTION = "collection"
LINK_REL_ITEM = "item"
LINK_REL_LICENSE = "license"
