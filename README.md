# DataCosmos SDK

## Overview
The **DataCosmos SDK** allows Open Cosmos' customers to interact with the main APIs required for creating applications that integrate with **DataCosmos**. This SDK provides authentication handling, HTTP request utilities, and a client for interacting with the **STAC API** (SpatioTemporal Asset Catalog).

## Installation

### Prerequisites
The SDK uses **uv** as a dependency manager. To install it:

```sh
pip install uv
```

### Setting Up the SDK
To install the SDK and its dependencies:

```sh
uv venv
uv pip install -r pyproject.toml
uv pip install -r pyproject.toml .[dev]
source .venv/bin/activate
```

## Authentication
The SDK requires authentication via a token stored in a `.netrc` file.

### Setting Up Authentication
Create the `.netrc` file:

```sh
touch ~/.netrc
```

Add the following content:

```
machine git.o-c.space
login __token__
password {provided_token}
```

You will need to **request** the token from Open Cosmos.

## Using the SDK

### Initializing the Client
The SDK provides the `DatacosmosClient` class to manage authentication and interact with the API.

```python
from datacosmos.client import DatacosmosClient

client = DatacosmosClient()
```

### STAC Client
The **STACClient** allows interaction with the STAC API, enabling search, retrieval, creation, updating, and deletion of STAC items.

#### Initialize STACClient

```python
from datacosmos.stac.stac_client import STACClient

stac_client = STACClient(client)
```

### STACClient Methods

#### 1. **Search Items**
```python
from datacosmos.stac.models.search_parameters import SearchParameters

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
from pystac import Item, Asset
from datetime import datetime

stac_item = Item(
    id="new-item",
    geometry={"type": "Point", "coordinates": [102.0, 0.5]},
    bbox=[101.0, 0.0, 103.0, 1.0],
    datetime=datetime.utcnow(),
    properties={},
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

stac_client.create_item(collection_id="example-collection", item=stac_item)
```

#### 5. **Update an Existing STAC Item**
```python
from datacosmos.stac.models.item_update import ItemUpdate
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

## Configuration
The SDK supports configuration via **YAML files** and **environment variables**.

- **YAML Configuration** (default: `config/config.yaml`)
- **Environment Variables** (e.g., `OC_AUTH_CLIENT_ID`, `OC_AUTH_CLIENT_SECRET`)

The SDK loads configuration settings automatically.

## Contributing
If you would like to contribute:
1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request.

Before making changes, ensure that:
- The code is formatted using **Black** and **isort**.
- Static analysis and linting are performed using **ruff** and **pydocstyle**.
- Security checks are performed using **bandit**.
- Tests are executed with **pytest**.

```sh
black .
isort .
ruff .
pydocstyle .
bandit -r .
pytest
```


