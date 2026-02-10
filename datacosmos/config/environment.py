"""Environment detection utilities for the Datacosmos SDK.

Provides functions to detect the runtime environment and return
appropriate configuration defaults.
"""

import os

from datacosmos.config.constants import (
    DEFAULT_STAC_EXTERNAL,
    DEFAULT_STAC_INTERNAL,
    DEFAULT_STORAGE_EXTERNAL,
    DEFAULT_STORAGE_INTERNAL,
    KUBERNETES_SERVICE_HOST_ENV,
)


def is_running_in_kubernetes() -> bool:
    """Detect if the SDK is running inside a Kubernetes cluster.

    Returns True if KUBERNETES_SERVICE_HOST environment variable is set,
    which is automatically injected by Kubernetes into all pods.
    """
    return KUBERNETES_SERVICE_HOST_ENV in os.environ


def get_default_stac() -> dict:
    """Get the default STAC URL based on environment.

    Returns internal cluster URLs when running in Kubernetes,
    otherwise returns external URLs.
    """
    return (
        DEFAULT_STAC_INTERNAL if is_running_in_kubernetes() else DEFAULT_STAC_EXTERNAL
    )


def get_default_storage() -> dict:
    """Get the default storage URL based on environment.

    Returns internal cluster URLs when running in Kubernetes,
    otherwise returns external URLs.
    """
    return (
        DEFAULT_STORAGE_INTERNAL
        if is_running_in_kubernetes()
        else DEFAULT_STORAGE_EXTERNAL
    )
