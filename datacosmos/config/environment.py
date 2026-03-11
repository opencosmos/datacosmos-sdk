"""Environment detection utilities for the Datacosmos SDK.

Provides functions to detect the runtime environment and return
appropriate configuration defaults.
"""

import os

from datacosmos.config.constants import (
    DEFAULT_PROJECT,
    DEFAULT_PROJECT_INTERNAL,
    DEFAULT_STAC_EXTERNAL,
    DEFAULT_STAC_INTERNAL,
    DEFAULT_STORAGE_EXTERNAL,
    DEFAULT_STORAGE_INTERNAL,
    OPENCOSMOS_INTERNAL_CLUSTER_ENV,
)


def is_running_in_opencosmos_cluster() -> bool:
    """Detect if the SDK is running inside Open Cosmos's internal cluster.

    Returns True if OPENCOSMOS_INTERNAL_CLUSTER environment variable is set.
    This variable must be explicitly set in Open Cosmos workflows/jobs
    to enable internal URL routing.

    Note: We do NOT use generic KUBERNETES_SERVICE_HOST detection because
    customers may run the SDK in their own K8s clusters, where Open Cosmos
    internal services are not available.
    """
    return os.environ.get(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "").lower() in (
        "true",
        "1",
        "yes",
    )


def get_default_stac() -> dict:
    """Get the default STAC URL based on environment.

    Returns internal cluster URLs when running in Open Cosmos's cluster,
    otherwise returns external URLs.
    """
    return (
        DEFAULT_STAC_INTERNAL
        if is_running_in_opencosmos_cluster()
        else DEFAULT_STAC_EXTERNAL
    )


def get_default_storage() -> dict:
    """Get the default storage URL based on environment.

    Returns internal cluster URLs when running in Open Cosmos's cluster,
    otherwise returns external URLs.
    """
    return (
        DEFAULT_STORAGE_INTERNAL
        if is_running_in_opencosmos_cluster()
        else DEFAULT_STORAGE_EXTERNAL
    )


def get_default_project() -> dict:
    """Get the default project URL based on environment.

    Returns internal cluster URLs when running in Open Cosmos's cluster,
    otherwise returns external URLs.
    """
    return (
        DEFAULT_PROJECT_INTERNAL
        if is_running_in_opencosmos_cluster()
        else DEFAULT_PROJECT
    )
