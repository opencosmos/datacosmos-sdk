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
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig

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
| `datacosmos_public_cloud_storage.protocol` | `https`                                 | YAML / ENV     |
| `datacosmos_public_cloud_storage.host`     | `app.open-cosmos.com`                   | YAML / ENV     |
| `datacosmos_public_cloud_storage.port`     | `443`                                   | YAML / ENV     |
| `datacosmos_public_cloud_storage.path`     | `/api/data/v0/storage`                 | YAML / ENV     |

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

#### 1. **Search Items**
```python
from datacosmos.stac.item.models.catalog_search_parameters import CatalogSearchParameters
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

params = CatalogSearchParameters(
     start_date="2/9/2025",
     end_date="2/9/2025",
     satellite=["MANTIS"],
     product_type=["Satellite"],
     processing_level=["L1A"],
     collections=["mantis-l1a"]
)

items = list(stac_client.search_items(parameters=params, project_id="your-project-id"))
```

#### 2. **Fetch a Single Item**
```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

item = stac_client.fetch_item(item_id="example-item", collection_id="example-collection")
```
#### 3. **Create a New STAC Item**
```python
from pystac import Item, Asset
from datetime import datetime

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

stac_item = Item(
    id="new-item",
    geometry={"type": "Point", "coordinates": [102.0, 0.5]},
    bbox=[101.0, 0.0, 103.0, 1.0],
    datetime=datetime.utcnow(),
    properties={"datetime": datetime.utcnow(), "processing:level": "example-processing-level"},
    collection="example-collection"
)

stac_item.add_asset(
    "image",
    Asset(
        href="https://example.com/sample-image.tiff",
        media_type="image/tiff",
        roles=["data"],
        title="Sample Image"
    )
)

# this will raise an error if the stac item already exists. Use the add_item method in that case
stac_client.create_item(item=stac_item)
```

#### 4. **Add a STAC Item**
```python
from pystac import Item, Asset
from datetime import datetime

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

stac_item = Item(
    id="new-item",
    geometry={"type": "Point", "coordinates": [102.0, 0.5]},
    bbox=[101.0, 0.0, 103.0, 1.0],
    datetime=datetime.utcnow(),
    properties={"datetime": datetime.utcnow(), "processing:level": "example-processing-level"},
    collection="example-collection"
)

stac_item.add_asset(
    "image",
    Asset(
        href="https://example.com/sample-image.tiff",
        media_type="image/tiff",
        roles=["data"],
        title="Sample Image"
    )
)

stac_client.add_item(item=stac_item)
```

#### 4. **Update an Existing STAC Item**
```python
from datacosmos.stac.item.models.item_update import ItemUpdate
from pystac import Asset, Link

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

update_payload = ItemUpdate(
    properties={
        "new_property": "updated_value",
        "datetime": "2024-11-10T14:58:00Z"
    },
    assets={
        "image": Asset(
            href="https://example.com/updated-image.tiff",
            media_type="image/tiff"
        )
    },
    links=[
        Link(rel="self", target="https://example.com/updated-image.tiff")
    ],
    geometry={
        "type": "Point",
        "coordinates": [10, 20]
    },
    bbox=[10.0, 20.0, 30.0, 40.0]
)

stac_client.update_item(item_id="new-item", collection_id="example-collection", update_data=update_payload)
```

#### 5. **Delete an Item**
```python

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

stac_client.delete_item(item_id="new-item", collection_id="example-collection")
```

#### 6. Fetch a Collection

```python

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

collection = stac_client.fetch_collection("test-collection")
```

#### 7. Fetch All Collections

```python

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

collections = list(stac_client.fetch_all_collections())
```

#### 8. Create a Collection

```python
from pystac import Collection

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

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

#### 9. Update a Collection

```python
from datacosmos.stac.collection.models.collection_update import CollectionUpdate

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

update_data = CollectionUpdate(
    title="Updated Collection Title",
    description="Updated description",
)

stac_client.update_collection("test-collection", update_data)
```

#### 10. Delete a Collection

```python

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

stac_client.delete_collection("test-collection")
```

## Uploading Files and Registering STAC Items

You can use the `STACClient` class to upload files to the DataCosmos cloud storage and register a STAC item.

### **Upload and add STAC Item**

```python
from pystac import Item, Asset

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()

stac_client = STACClient(client)

stac_item = Item(
    id="new-item",
    geometry={"type": "Point", "coordinates": [102.0, 0.5]},
    bbox=[101.0, 0.0, 103.0, 1.0],
    datetime=datetime.utcnow(),
    properties={"datetime": datetime.utcnow(), "processing:level": "example-processing-level"},
    collection="example-collection"
)

stac_item.add_asset(
    "image",
    Asset(
        href="https://example.com/sample-image.tiff",
        media_type="image/tiff",
        roles=["data"],
        title="Sample Image"
    )
)

assets_path = "path/to/assets"

# Upload the item and its assets, and register it in the STAC API
stac_client.upload_item(stac_item, assets_path)
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
