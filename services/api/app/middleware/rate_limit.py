from slowapi import Limiter
from slowapi.util import get_remote_address


def get_rate_limit_key(request):
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return f"tenant:{tenant_id}"
    return get_remote_address(request)


# Create rate limiter (per-tenant when available, fallback to IP)
limiter = Limiter(key_func=get_rate_limit_key)
