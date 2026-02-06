# CHANGELOG
## [1.0.0] - Unreleased

### ⚠️ Breaking Changes

- **`DatacosmosItem.bbox`**: Changed type from `tuple` to `list[float]`. Update any code passing tuples to use lists instead.
- **`STACClient.upload_item()` `assets_path` parameter**: Changed type from `Path | str | None` to `str | None`. Convert `Path` objects to strings before passing.
- **`STACClient.upload_item()` return type**: Now returns `UploadResult` object with `succeeded` and `failed` asset lists instead of `None`.
- **`Config` URL fields**: Fields `stac`, `datacosmos_cloud_storage`, and `datacosmos_public_cloud_storage` now use `URL` model type (strings are auto-coerced).

### Added

- STAC 1.1.0 specification support
- `UploadResult` model for tracking upload success/failure per asset
- `Statistics` and `Band` models for enhanced Asset metadata
- New optional Asset fields: `keywords`, `data_type`, `nodata`, `unit`, `statistics`, `bands`

### Changed

- `DatacosmosItem` validation now enforces required properties: `datetime`, `created_by`, `sat:platform_international_designator`
- Geometry validation requires correct winding order for Polygon/MultiPolygon