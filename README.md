# DataCosmos SDK

## Overview

The **DataCosmos SDK** allows Open Cosmos' customers to interact with the **DataCosmos APIs** for seamless data management and retrieval. It provides authentication handling, HTTP request utilities, and a client for interacting with the **STAC API** (SpatioTemporal Asset Catalog).

## Installation

### Install via PyPI

The easiest way to install the SDK is via **pip**:

```sh
pip install datacosmos=={version}
```

## Getting Started

### Initializing the Client

The recommended way to initialize the SDK is by passing a `Config` object with authentication credentials:

```python
from datacosmos.datacosmos_client import DatacosmosClient
from config.config import Config

config = Config(
    authentication={
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "token_url": "https://login.open-cosmos.com/oauth/token",
        "audience": "https://beeapp.open-cosmos.com"
    }
)
client = DatacosmosClient(config=config)
```

Alternatively, the SDK can load configuration automatically from:

- A YAML file (`config/config.yaml`)
- Environment variables

### STAC Client

The STACClient enables interaction with the STAC API, allowing for searching, retrieving, creating, updating, and deleting STAC items and collections.

#### Initialize STACClient

```python
from datacosmos.stac.stac_client import STACClient

stac_client = STACClient(client)
```

### STACClient Methods

#### 1. **Fetch a Collection**

```python
from datacosmos.stac.stac_client import STACClient
from datacosmos.datacosmos_client import DatacosmosClient

datacosmos_client = DatacosmosClient()
stac_client = STACClient(datacosmos_client)

collection = stac_client.fetch_collection("test-collection")
```

#### 2. **Fetch All Collections**

```python
collections = list(stac_client.fetch_all_collections())
```

#### 3. **Create a Collection**

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

#### 4. **Update a Collection**

```python
from datacosmos.stac.collection.models.collection_update import CollectionUpdate

update_data = CollectionUpdate(
    title="Updated Collection Title version 2",
    description="Updated description version 2",
)

stac_client.update_collection("test-collection", update_data)
```

#### 5. **Delete a Collection**

```python
collection_id = "test-collection"
stac_client.delete_collection(collection_id)
```

#### 1. **Search Items**

```python
from datacosmos.stac.item.models.search_parameters import SearchParameters

parameters = SearchParameters(collections=["example-collection"], limit=1)
items = list(stac_client.search_items(parameters=parameters))
```

#### 2. **Fetch a Single Item**

```python
item = stac_client.fetch_item(item_id="example-item", collection_id="example-collection")
```

#### 3. **Fetch All Items in a Collection**

```python
items = stac_client.fetch_collection_items(collection_id="example-collection")
```

#### 4. **Create a New STAC Item**

```python
from datetime import datetime
from pystac import Item, Asset
from pystac.utils import str_to_datetime

stac_item = Item(
    id="MENUT_000001418_20240211120920_20240211120932_new_release.tiff",
    geometry={
        "type": "Polygon",
        "coordinates": [
            [
                [-24.937406454761664, 64.5931773445667],
                [-19.6596824245997, 64.5931773445667],
                [-19.6596824245997, 63.117895100111724],
                [-24.937406454761664, 63.117895100111724],
                [-24.937406454761664, 64.5931773445667]
            ]
        ]
    },
    bbox=[
        -24.937406454761664,
        63.117895100111724,
        -19.6596824245997,
        64.5931773445667
    ],
    datetime=str_to_datetime("2024-02-11T12:09:32Z"),
    properties={"processing:level": "L0"},
    collection="menut-l0",
)

stac_item.add_asset(
    "thumbnail",
    Asset(
        href="https://test.app.open-cosmos.com/api/data/v0/storage/full/menut/l0/2024/02/11/MENUT_000001418_20240211120920_20240211120932.tiff/thumbnail.webp",
        media_type="image/webp",
        roles=["thumbnail"],
        title="Thumbnail",
        description="Thumbnail of the image"
    )
)

stac_client.create_item(collection_id="menutl-l0", item=stac_item)
```

#### 5. **Update an Existing STAC Item**

```python
from datacosmos.stac.item.models.item_update import ItemUpdate
from pystac import Asset, Link

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

#### 6. **Delete an Item**

```python
stac_client.delete_item(item_id="new-item", collection_id="example-collection")
```

## Configuration Options

- **Recommended:** Instantiate `DatacosmosClient` with a `Config` object.
- Alternatively, use **YAML files** (`config/config.yaml`).
- Or, use **environment variables**.

## Contributing

If you would like to contribute:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request.

### Development Setup

If you are developing the SDK, you can use `uv` for dependency management:

```sh
pip install uv
uv venv
uv pip install -r pyproject.toml
uv pip install -r pyproject.toml .[dev]
source .venv/bin/activate
```

Before making changes, ensure that:

- The code is formatted using **Black** and **isort**.
- Static analysis and linting are performed using **ruff** and **pydocstyle**.
- Security checks are performed using **bandit**.
- Tests are executed with **pytest**.

```sh
black .
isort .
ruff check . --select C901
pydocstyle .
bandit -r -c pyproject.toml . --skip B105,B106,B101
pytest
```
