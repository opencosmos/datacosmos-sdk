# DataCosmos SDK

## Overview

The **DataCosmos SDK** enables Open Cosmos customers to interact with the **DataCosmos APIs** for efficient data management and retrieval. It provides authentication handling, HTTP request utilities, and a client for interacting with the **STAC API** (SpatioTemporal Asset Catalog).

## Installation

Install the SDK using **pip**:

```sh
pip install datacosmos=={version}
```

## Initializing the Client

To start using the SDK, initialize the client. The easiest way to do this is by loading the configuration from a YAML file. Alternatively, you can manually instantiate the Config object or use environment variables.

### Default Initialization (Recommended)

By default, the client loads configuration from a YAML file (`config/config.yaml`).

```python
from datacosmos.datacosmos_client import DatacosmosClient

client = DatacosmosClient()
```

### Loading from YAML (Recommended)

Create a YAML file (`config/config.yaml`) with the following content:

```yaml
authentication:
    client_id: {client_id}  
    client_secret: {client_secret}
```

The client will automatically read this file when initialized.

### Loading from Environment Variables

Set the following environment variables:

```sh
export OC_AUTH_CLIENT_ID={client_id}
export OC_AUTH_CLIENT_SECRET={client_secret}
```

The client will automatically read these values when initialized.

### Manual Instantiation

If manually instantiating `Config`, default values are now applied where possible.

```python
from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from config.models.url import URL

config = Config(
    authentication=M2MAuthenticationConfig(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
)

client = DatacosmosClient(config=config)
```

### Configuration Options and Defaults

| Setting                      | Default Value                                     | Override Method |
|------------------------------|-------------------------------------------------|----------------|
| `authentication.type`        | `m2m`                                           | YAML / ENV     |
| `authentication.client_id`   | _Required in manual instantiation_              | YAML / ENV     |
| `authentication.client_secret` | _Required in manual instantiation_            | YAML / ENV     |
| `stac.protocol`              | `https`                                         | YAML / ENV     |
| `stac.host`                  | `app.open-cosmos.com`                           | YAML / ENV     |
| `stac.port`                  | `443`                                           | YAML / ENV     |
| `stac.path`                  | `/api/data/v0/stac`                             | YAML / ENV     |
| `datacosmos_cloud_storage.protocol` | `https`                                 | YAML / ENV     |
| `datacosmos_cloud_storage.host`     | `app.open-cosmos.com`                   | YAML / ENV     |
| `datacosmos_cloud_storage.port`     | `443`                                   | YAML / ENV     |
| `datacosmos_cloud_storage.path`     | `/api/data/v0/storage`                 | YAML / ENV     |
| `mission_id`                | `0`                                             | YAML / ENV     |
| `environment`               | `test`                                          | YAML / ENV     |

## STAC Client

The `STACClient` enables interaction with the STAC API, allowing for searching, retrieving, creating, updating, and deleting STAC items and collections.

### Initialize STACClient

```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)
```

### STACClient Methods

#### 1. Fetch a Collection

```python
collection = stac_client.fetch_collection("test-collection")
```

#### 2. Fetch All Collections

```python
collections = list(stac_client.fetch_all_collections())
```

#### 3. Create a Collection

```python
from pystac import Collection

new_collection = Collection(
    id="test-collection",
    title="Test Collection",
    description="This is a test collection",
    license="proprietary",
    extent={
        "spatial": {"bbox": [[-180, -90, 180, 90]]},
        "temporal": {"interval": [["2023-01-01T00:00:00Z", None]]},
    },
)

stac_client.create_collection(new_collection)
```

#### 4. Update a Collection

```python
from datacosmos.stac.collection.models.collection_update import CollectionUpdate

update_data = CollectionUpdate(
    title="Updated Collection Title",
    description="Updated description",
)

stac_client.update_collection("test-collection", update_data)
```

#### 5. Delete a Collection

```python
stac_client.delete_collection("test-collection")
```

### Uploading Files and Registering STAC Items

You can use the `DatacosmosUploader` class to upload files to the DataCosmos cloud storage and register a STAC item.

#### Upload Files and Register STAC Item

```python
from datacosmos.uploader.datacosmos_uploader import DatacosmosUploader

uploader = DatacosmosUploader(client)
item_json_file_path = "/path/to/stac_item.json"
uploader.upload_and_register_item(item_json_file_path)
```

## Error Handling

Use `try-except` blocks to handle API errors gracefully:

```python
try:
    data = client.get_data("dataset_id")
    print(data)
except Exception as e:
    print(f"An error occurred: {e}")
```

## Contributing

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request.

### Development Setup

Use `uv` for dependency management:

```sh
pip install uv
uv venv
uv pip install -r pyproject.toml .[dev]
source .venv/bin/activate
```

Before making changes, run:

```sh
black .
isort .
ruff check .
pydocstyle .
bandit -r -c pyproject.toml .
pytest
```
