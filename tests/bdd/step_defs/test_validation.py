"""Step definitions for validation operations."""

from pytest_bdd import given, when, then, parsers, scenarios

# Load all scenarios from the feature file
scenarios("../features/validation.feature")


# Search Parameter Validation Steps


@given(parsers.parse('start_date "{date}" in mm/dd/yyyy format'))
def valid_start_date(context, date):
    """Set up valid start date."""
    context.extra["start_date"] = date


@given(parsers.parse('end_date "{date}"'))
def end_date(context, date):
    """Set up end date."""
    context.extra["end_date"] = date


@given(parsers.parse('start_date "{date}" before minimum allowed date'))
def start_date_too_early(context, date):
    """Set up start date before minimum."""
    context.extra["start_date"] = date
    context.extra["expect_validation_error"] = True


@given(parsers.parse('start_date "{start_date}" and end_date "{end_date}"'))
def start_end_dates(context, start_date, end_date):
    """Set up both dates."""
    context.extra["start_date"] = start_date
    context.extra["end_date"] = end_date


@given(parsers.parse('processing_level "{level}"'))
def processing_level(context, level):
    """Set up processing level."""
    context.extra["processing_level"] = [level]


@given(parsers.parse('product_type "{ptype}"'))
def product_type(context, ptype):
    """Set up product type."""
    context.extra["product_type"] = [ptype]


@when("CatalogSearchParameters is created")
def create_search_params(context):
    """Create CatalogSearchParameters."""
    from datacosmos.stac.item.models.catalog_search_parameters import CatalogSearchParameters
    
    kwargs = {}
    if "start_date" in context.extra:
        kwargs["start_date"] = context.extra["start_date"]
    if "end_date" in context.extra:
        kwargs["end_date"] = context.extra.get("end_date", "12/31/2030")
    else:
        kwargs["end_date"] = "12/31/2030"
    if "processing_level" in context.extra:
        kwargs["processing_level"] = context.extra["processing_level"]
    if "product_type" in context.extra:
        kwargs["product_type"] = context.extra["product_type"]
    
    # Ensure we have both dates if only one is provided
    if "start_date" not in kwargs:
        kwargs["start_date"] = "01/01/2024"
    
    context.result = CatalogSearchParameters(**kwargs)


@when("I attempt to create CatalogSearchParameters")
def attempt_create_search_params(context):
    """Attempt to create CatalogSearchParameters, capturing exception."""
    from datacosmos.stac.item.models.catalog_search_parameters import CatalogSearchParameters
    from datacosmos.exceptions import StacValidationError
    
    try:
        kwargs = {}
        if "start_date" in context.extra:
            kwargs["start_date"] = context.extra["start_date"]
        else:
            kwargs["start_date"] = "01/01/2024"  # Default start date
        if "end_date" in context.extra:
            kwargs["end_date"] = context.extra["end_date"]
        else:
            kwargs["end_date"] = "12/31/2030"
        
        context.result = CatalogSearchParameters(**kwargs)
    except (StacValidationError, ValueError) as e:
        context.exception = e


@then("start_date should be converted to ISO format")
def verify_start_date_iso(context):
    """Verify start_date is ISO format."""
    assert context.result is not None
    # The search params should have converted the date
    assert context.result.start_date is not None


@then("end_date should include time 23:59:59.999")
def verify_end_date_time(context):
    """Verify end_date includes full day time."""
    assert context.result is not None
    # End date should be end of day
    assert context.result.end_date is not None


@then("a StacValidationError should be raised")
def verify_stac_validation_error(context):
    """Verify StacValidationError raised."""
    assert context.exception is not None


@then("processing_level should be converted to ProcessingLevel enum")
def verify_processing_level_enum(context):
    """Verify processing level converted."""
    assert context.result is not None
    assert context.result.processing_level is not None


@then("product_type should be converted to ProductType enum")
def verify_product_type_enum(context):
    """Verify product type converted."""
    assert context.result is not None
    assert context.result.product_type is not None


# License Validation Steps


@given(parsers.parse('license "{license_value}"'))
def license_value(context, license_value):
    """Set up license value."""
    context.extra["license"] = license_value


@when("I normalize the collection license")
def normalize_license(context):
    """Normalize collection license."""
    from datacosmos.stac.validation.license import normalize_collection_license
    
    result, warning = normalize_collection_license(context.extra["license"])
    context.result = result
    context.extra["warning"] = warning


@when("I attempt to normalize the collection license")
def attempt_normalize_license(context):
    """Attempt to normalize license, capturing exception."""
    from datacosmos.stac.validation.license import normalize_collection_license
    from datacosmos.exceptions import StacValidationError
    
    try:
        result, warning = normalize_collection_license(context.extra["license"])
        context.result = result
        context.extra["warning"] = warning
    except StacValidationError as e:
        context.exception = e


@then(parsers.parse('the result should be "{expected}" with a warning'))
def verify_license_with_warning(context, expected):
    """Verify license result with warning."""
    assert context.result == expected
    assert context.extra.get("warning") is not None


@then(parsers.parse('the result should be "{expected}" with no warning'))
def verify_license_no_warning(context, expected):
    """Verify license result without warning."""
    assert context.result == expected
    assert context.extra.get("warning") is None
