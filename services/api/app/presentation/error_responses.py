"""Shared error responses for OpenAPI documentation."""

ERROR_RESPONSE_SCHEMA = {"$ref": "#/components/schemas/ErrorResponse"}

DEFAULT_ERROR_RESPONSES = {
    400: {
        "description": "Bad Request",
        "content": {"application/json": {"schema": ERROR_RESPONSE_SCHEMA}},
    },
    401: {
        "description": "Unauthorized",
        "content": {"application/json": {"schema": ERROR_RESPONSE_SCHEMA}},
    },
    403: {
        "description": "Forbidden",
        "content": {"application/json": {"schema": ERROR_RESPONSE_SCHEMA}},
    },
    404: {
        "description": "Not Found",
        "content": {"application/json": {"schema": ERROR_RESPONSE_SCHEMA}},
    },
    409: {
        "description": "Conflict",
        "content": {"application/json": {"schema": ERROR_RESPONSE_SCHEMA}},
    },
    422: {
        "description": "Validation Error",
        "content": {"application/json": {"schema": ERROR_RESPONSE_SCHEMA}},
    },
    429: {
        "description": "Too Many Requests",
        "content": {"application/json": {"schema": ERROR_RESPONSE_SCHEMA}},
    },
    500: {
        "description": "Internal Server Error",
        "content": {"application/json": {"schema": ERROR_RESPONSE_SCHEMA}},
    },
}
