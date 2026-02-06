import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.domain.entities.farm import Farm
from app.domain.value_objects.tenant_id import TenantId


def test_farm_validates_name_length():
    with pytest.raises(ValidationError):
        Farm(tenant_id=TenantId(value=uuid4()), name="AB")


def test_farm_validates_reserved_name():
    with pytest.raises(ValidationError):
        Farm(tenant_id=TenantId(value=uuid4()), name="admin")


def test_farm_validates_on_update():
    farm = Farm(tenant_id=TenantId(value=uuid4()), name="Valid Name")

    with pytest.raises(ValidationError):
        farm.name = "X"
