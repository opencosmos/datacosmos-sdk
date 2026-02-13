# Open Cosmos Cluster URL Auto-Detection Test

This directory contains resources to test the Open Cosmos cluster URL auto-detection feature.

## How It Works

The SDK uses a custom environment variable `OPENCOSMOS_INTERNAL_CLUSTER` to detect when it's running inside Open Cosmos's Kubernetes cluster. This is intentionally **not** based on generic Kubernetes detection (`KUBERNETES_SERVICE_HOST`) because:

- Customers may run the SDK in their own K8s clusters
- Open Cosmos internal services (`catalog.default.svc.cluster.local`, etc.) are only accessible from within Open Cosmos's cluster
- Using generic K8s detection would cause failures for customers running in their own clusters

## Quick Start

1. **Deploy the test job:**
   ```bash
   kubectl apply -f k8s-test/test-job.yaml
   ```

2. **Watch the job status:**
   ```bash
   kubectl get jobs datacosmos-oc-cluster-test -w
   ```

3. **View the test output:**
   ```bash
   kubectl logs job/datacosmos-oc-cluster-test
   ```

4. **Clean up:**
   ```bash
   kubectl delete job datacosmos-oc-cluster-test
   ```

## What the Test Verifies

The test script (`test-k8s-detection.py`) verifies:

1. **Environment Detection**: `is_running_in_opencosmos_cluster()` returns `True` when `OPENCOSMOS_INTERNAL_CLUSTER=true` is set

2. **Internal URLs**: `stac` and `datacosmos_cloud_storage` default to internal cluster URLs:
   - `http://catalog.default.svc.cluster.local:80/`
   - `http://storage.default.svc.cluster.local:80/`

3. **Public URLs Preserved**: `datacosmos_public_cloud_storage` still uses external URLs:
   - `https://app.open-cosmos.com:443/api/data/v0/storage`
   - This ensures asset hrefs in STAC items are always public URLs

## Expected Output

```
============================================================
Open Cosmos Cluster URL Auto-Detection Test
============================================================

Environment:
  OPENCOSMOS_INTERNAL_CLUSTER: true
  KUBERNETES_SERVICE_HOST: 10.x.x.x

Environment Detection:
  is_running_in_opencosmos_cluster(): True

Default URLs (should be internal):
  get_default_stac():    {'protocol': 'http', 'host': 'catalog.default.svc.cluster.local', ...}
  get_default_storage(): {'protocol': 'http', 'host': 'storage.default.svc.cluster.local', ...}

Config class test:
  stac:                 http://catalog.default.svc.cluster.local:80/
  cloud_storage:        http://storage.default.svc.cluster.local:80/
  public_cloud_storage: https://app.open-cosmos.com:443/api/data/v0/storage

============================================================
✅ ALL TESTS PASSED
  - Open Cosmos cluster detection works correctly
  - Internal URLs are used for stac and cloud_storage
  - External URL is preserved for public_cloud_storage
```

## Enabling Internal URLs in Your Workflows

To enable internal URL routing in Open Cosmos workflows, add this environment variable to your container spec:

```yaml
env:
  - name: OPENCOSMOS_INTERNAL_CLUSTER
    value: "true"
```

## Testing Locally

```bash
# Should use external URLs (not in OC cluster)
python k8s-test/test-k8s-detection.py

# Simulate Open Cosmos cluster
OPENCOSMOS_INTERNAL_CLUSTER=true python k8s-test/test-k8s-detection.py
```
