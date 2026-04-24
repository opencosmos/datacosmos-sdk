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

### Using a Pre-obtained Token

If you already have an access token (e.g., from an external authentication flow), you can pass it directly:

```python
from datacosmos.datacosmos_client import DatacosmosClient

client = DatacosmosClient(token="your-access-token")
```

**Note:** When using a token directly, the client will not attempt to refresh it automatically. You are responsible for managing token expiration.

### Using a Pre-authenticated Session

For advanced use cases where you manage your own HTTP session (e.g., with custom middleware or authentication), you can inject it:

```python
import requests
from datacosmos.datacosmos_client import DatacosmosClient

# Create a session with your own authentication setup
session = requests.Session()
session.headers.update({"Authorization": "Bearer your-token"})

client = DatacosmosClient(http_session=session)
```

You can also use an OAuth2Session:

```python
from requests_oauthlib import OAuth2Session
from datacosmos.datacosmos_client import DatacosmosClient

oauth_session = OAuth2Session(client_id="your-client-id")
oauth_session.token = {
    "access_token": "your-access-token",
    "expires_in": 3600
}

client = DatacosmosClient(http_session=oauth_session)
```

### Local User Authentication (Interactive)

For interactive local development, you can use browser-based authentication:

```yaml
# config/config.yaml
authentication:
    type: local
    client_id: {client_id}
```

This opens a browser window for login and caches the token locally at `~/.datacosmos/token_cache.json`.

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
| `project.protocol`                         | `https`                                 | YAML / ENV     |
| `project.host`                             | `app.open-cosmos.com`                   | YAML / ENV     |
| `project.port`                             | `443`                                   | YAML / ENV     |
| `project.path`                             | `/api/data/v0/scenario`                 | YAML / ENV     |

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

### Project Item Operations

The `STACClient` also provides methods to interact with project/scenario items. Projects (also called scenarios) are collections of STAC items that can include both linked catalog items and project-specific items.

#### 11. List Project Items

List all items in a project/scenario:

```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

scenario_id = "your-scenario-uuid"
items = list(stac_client.list_project_items(scenario_id))

for item in items:
    print(f"{item.id} (collection: {item.collection_id})")
```

#### 12. Get a Project Item

Fetch a specific item from a project:

```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

scenario_id = "your-scenario-uuid"
item_id = "your-item-id"

item = stac_client.get_project_item(scenario_id, item_id)
print(f"Item: {item.id}")
```

#### 13. Add an Item to a Project

Add or update an item in a project (upsert):

```python
from pystac import Item
from datetime import datetime

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

scenario_id = "your-scenario-uuid"

item = Item(
    id="my-item-id",
    geometry={"type": "Point", "coordinates": [102.0, 0.5]},
    bbox=[101.0, 0.0, 103.0, 1.0],
    datetime=datetime.utcnow(),
    properties={},
)

stac_client.add_project_item(scenario_id, item)
```

#### 14. Create a Project Item

Create a new STAC item directly in a project:

```python
from pystac import Item
from datetime import datetime

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

scenario_id = "your-scenario-uuid"

stac_item = Item(
    id="new-project-item",
    geometry={"type": "Point", "coordinates": [102.0, 0.5]},
    bbox=[101.0, 0.0, 103.0, 1.0],
    datetime=datetime.utcnow(),
    properties={"datetime": datetime.utcnow().isoformat()},
)

stac_client.create_project_item(scenario_id, stac_item)
```

#### 15. Delete a Project Item

Remove an item from a project:

```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

scenario_id = "your-scenario-uuid"
item_id = "item-to-delete"

stac_client.delete_project_item(scenario_id, item_id)
```

#### 16. Search Project Items

Search for items within a project with optional filters:

```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient
from datacosmos.stac.project.models.project_search_parameters import ProjectSearchParameters

client = DatacosmosClient()
stac_client = STACClient(client)

scenario_id = "your-scenario-uuid"

# Search with parameters
params = ProjectSearchParameters(
    collections=["specific-collection"],
    limit=10
)

results = list(stac_client.search_project_items(scenario_id, params))
for item in results:
    print(f"{item.id}")
```

#### 17. Check if Items Exist in a Project

Check if specific catalog items are linked to a project:

```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient
from datacosmos.stac.project.models.collection_item_pair import CollectionItemPair

client = DatacosmosClient()
stac_client = STACClient(client)

scenario_id = "your-scenario-uuid"

pairs = [
    CollectionItemPair(collection="collection-1", item="item-1"),
    CollectionItemPair(collection="collection-2", item="item-2"),
]

existence = stac_client.check_project_items_exist(scenario_id, pairs)
for result in existence:
    print(f"{result.collection}/{result.item}: exists={result.exists}")
```

#### 18. Register a Catalog Item to a Project

Link an existing catalog item to a project. This creates a relation between the item and the project without copying the item:

```python
from pystac import Item
from datetime import datetime

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

project_id = "your-project-uuid"

# First, create/add the item to the catalog
stac_item = Item(
    id="catalog-item",
    geometry={"type": "Point", "coordinates": [102.0, 0.5]},
    bbox=[101.0, 0.0, 103.0, 1.0],
    datetime=datetime.utcnow(),
    properties={"processing:level": "l1a"},
    collection="my-collection"
)
stac_client.add_item(stac_item)

# Then register/link it to a project
stac_client.register_item_to_project(stac_item, project_id)
```

This is useful when you want to associate existing catalog items with a project without duplicating the data.

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

### Download Assets

Download all assets of a STAC item to a local directory:

```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

# Download assets for an item
item, successes, failures = stac_client.download_assets(
    item="item-id",
    collection_id="collection-id",
    target_path="./downloads",
    included_assets=True,  # True for all assets, or list of asset keys
    overwrite=True,
    max_workers=4
)

print(f"Downloaded {len(successes)} assets")
if failures:
    print(f"Failed: {failures}")
```

### Delete Item with Assets

Delete a STAC item and optionally remove its assets from storage:

```python
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

client = DatacosmosClient()
stac_client = STACClient(client)

# Delete item and all its assets from storage
result = stac_client.delete_item_with_assets(
    item_id="item-id",
    collection_id="collection-id",
    delete_from_storage=True,  # Set to False to keep files in storage
    max_workers=4
)

print(f"Item deleted: {result.item_deleted}")
print(f"Assets deleted: {result.assets_deleted}")
print(f"Assets failed: {result.assets_failed}")
```

### Load and Save Items

Utility methods for working with STAC items as JSON files:

```python
from datacosmos.stac.storage.uploader import Uploader

# Load an item from a JSON file
item = Uploader.load_item("./data/my-item.json")

# Save an item to a directory (creates {item.id}.json)
saved_path = Uploader.save_item(item, "./output")
print(f"Saved to: {saved_path}")
```

## Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from datacosmos.exceptions import (
    AuthenticationError,
    DatacosmosError,
    HTTPError,
    ItemNotFoundError,
    CollectionError,
    DeleteError,
    StorageError,
    UploadError,
    StacValidationError,
)

try:
    item = stac_client.fetch_item(item_id="missing", collection_id="col")
except ItemNotFoundError:
    print("Item does not exist")
except AuthenticationError:
    print("Authentication failed - check your credentials")
except HTTPError as e:
    print(f"HTTP error: {e.status_code} - {e.message}")
except DatacosmosError as e:
    print(f"General API error: {e}")
```

### Exception Types

| Exception | When Raised |
|-----------|-----------|
| `AuthenticationError` | Authentication fails (invalid credentials, expired token) |
| `HTTPError` | Non-2xx HTTP response from the API |
| `ItemNotFoundError` | Requested STAC item does not exist |
| `CollectionError` | Collection operation fails |
| `DeleteError` | Delete operation fails |
| `StorageError` | Storage operation fails (upload/download) |
| `UploadError` | File upload fails |
| `StacValidationError` | STAC item/collection validation fails |
| `DatacosmosError` | Base exception for all SDK errors |

## Advanced Features

### Request and Response Hooks

You can add custom hooks to intercept requests and responses for logging, metrics, or custom processing:

```python
from datacosmos.datacosmos_client import DatacosmosClient

def log_request(method, url, *args, **kwargs):
    print(f"Request: {method} {url}")

def log_response(response):
    print(f"Response: {response.status_code}")

client = DatacosmosClient(
    config={...},
    request_hooks=[log_request],
    response_hooks=[log_response]
)
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
