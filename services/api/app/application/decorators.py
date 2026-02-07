"""Application-layer decorators."""
from __future__ import annotations

import inspect
from functools import wraps


def _validate_tenant(command) -> None:
    if command is None:
        raise ValueError("tenant_id is required")

    tenant_id = getattr(command, "tenant_id", None)
    if tenant_id is None:
        raise ValueError("tenant_id is required")

    value = getattr(tenant_id, "value", tenant_id)
    if value is None or value == "":
        raise ValueError("tenant_id is required")


def require_tenant(func):
    """Ensure tenant_id is present on command objects."""
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(self, command, *args, **kwargs):
            _validate_tenant(command)
            return await func(self, command, *args, **kwargs)

        return wrapper

    @wraps(func)
    def wrapper(self, command, *args, **kwargs):
        _validate_tenant(command)
        return func(self, command, *args, **kwargs)

    return wrapper
