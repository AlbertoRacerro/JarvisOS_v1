from enum import StrEnum


class LocalGemmaFailureCode(StrEnum):
    runtime_unavailable = "runtime_unavailable"
    local_endpoint_invalid = "local_endpoint_invalid"
    timeout = "timeout"
    invalid_json = "invalid_json"
    schema_invalid = "schema_invalid"
    prose_instead_of_schema = "prose_instead_of_schema"
    unexpected_local_http_error = "unexpected_local_http_error"


class LocalGemmaConfigurationError(ValueError):
    """Raised when a local Gemma dry-run configuration is unsafe."""
