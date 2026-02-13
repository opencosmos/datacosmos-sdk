#!/usr/bin/env python3
"""
Test script to verify Open Cosmos cluster URL auto-detection works.

This script will be run inside an Open Cosmos K8s pod to verify that:
1. is_running_in_opencosmos_cluster() returns True when OPENCOSMOS_INTERNAL_CLUSTER is set
2. stac and datacosmos_cloud_storage use internal URLs
3. datacosmos_public_cloud_storage still uses external URLs (for public asset hrefs)
"""

import os
import sys


def main():
    print("=" * 60)
    print("Open Cosmos Cluster URL Auto-Detection Test")
    print("=" * 60)

    # Check environment
    oc_cluster = os.environ.get("OPENCOSMOS_INTERNAL_CLUSTER", "NOT SET")
    k8s_host = os.environ.get("KUBERNETES_SERVICE_HOST", "NOT SET")
    print(f"\nEnvironment:")
    print(f"  OPENCOSMOS_INTERNAL_CLUSTER: {oc_cluster}")
    print(f"  KUBERNETES_SERVICE_HOST: {k8s_host}")

    # Test the environment detection
    from datacosmos.config.environment import (
        is_running_in_opencosmos_cluster,
        get_default_stac,
        get_default_storage,
    )
    from datacosmos.config.constants import (
        DEFAULT_STAC_INTERNAL,
        DEFAULT_STORAGE_INTERNAL,
    )

    print(f"\nEnvironment Detection:")
    in_oc_cluster = is_running_in_opencosmos_cluster()
    print(f"  is_running_in_opencosmos_cluster(): {in_oc_cluster}")

    if not in_oc_cluster:
        print("\n❌ ERROR: Expected OPENCOSMOS_INTERNAL_CLUSTER to be set!")
        print("    Set OPENCOSMOS_INTERNAL_CLUSTER=true in your pod spec.")
        sys.exit(1)

    print(f"\nDefault URLs (should be internal):")
    stac_url = get_default_stac()
    storage_url = get_default_storage()
    print(f"  get_default_stac():    {stac_url}")
    print(f"  get_default_storage(): {storage_url}")

    # Verify URLs are internal
    errors = []
    if stac_url != DEFAULT_STAC_INTERNAL:
        errors.append(f"stac URL should be {DEFAULT_STAC_INTERNAL}, got {stac_url}")
    if storage_url != DEFAULT_STORAGE_INTERNAL:
        errors.append(f"storage URL should be {DEFAULT_STORAGE_INTERNAL}, got {storage_url}")

    # Test Config class
    print(f"\nConfig class test:")
    from datacosmos.config.config import Config
    from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig

    # Create config with dummy auth (we're just testing URL defaults)
    cfg = Config(
        authentication=M2MAuthenticationConfig(
            client_id="test-client", client_secret="test-secret"
        )
    )

    stac_full = (
        f"{cfg.stac.protocol}://{cfg.stac.host}:{cfg.stac.port}{cfg.stac.path}"
    )
    storage_full = f"{cfg.datacosmos_cloud_storage.protocol}://{cfg.datacosmos_cloud_storage.host}:{cfg.datacosmos_cloud_storage.port}{cfg.datacosmos_cloud_storage.path}"
    public_storage_full = f"{cfg.datacosmos_public_cloud_storage.protocol}://{cfg.datacosmos_public_cloud_storage.host}:{cfg.datacosmos_public_cloud_storage.port}{cfg.datacosmos_public_cloud_storage.path}"

    print(f"  stac:                 {stac_full}")
    print(f"  cloud_storage:        {storage_full}")
    print(f"  public_cloud_storage: {public_storage_full}")

    # Verify config URLs
    if "cluster.local" not in stac_full:
        errors.append(f"Config stac should use internal URL, got {stac_full}")
    if "cluster.local" not in storage_full:
        errors.append(f"Config cloud_storage should use internal URL, got {storage_full}")
    if "cluster.local" in public_storage_full:
        errors.append(
            f"Config public_cloud_storage should NOT use internal URL, got {public_storage_full}"
        )
    if "app.open-cosmos.com" not in public_storage_full:
        errors.append(
            f"Config public_cloud_storage should use external URL, got {public_storage_full}"
        )

    # Report results
    print("\n" + "=" * 60)
    if errors:
        print("❌ TEST FAILED")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ ALL TESTS PASSED")
        print("  - Open Cosmos cluster detection works correctly")
        print("  - Internal URLs are used for stac and cloud_storage")
        print("  - External URL is preserved for public_cloud_storage")
        sys.exit(0)


if __name__ == "__main__":
    main()
