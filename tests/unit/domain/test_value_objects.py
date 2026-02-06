import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt
from app.domain.value_objects.tenant_id import TenantId
from app.domain.value_objects.user_id import UserId


def test_tenant_id_requires_uuid():
    tenant_id = TenantId(value=uuid4())
    assert tenant_id.value is not None


def test_user_id_requires_uuid():
    user_id = UserId(value=uuid4())
    assert user_id.value is not None


def test_geometry_wkt_rejects_invalid_prefix():
    with pytest.raises(ValidationError):
        GeometryWkt(value="LINESTRING (0 0, 1 1)")


def test_area_hectares_rejects_negative():
    with pytest.raises(ValidationError):
        AreaHectares(value=-1.0)
