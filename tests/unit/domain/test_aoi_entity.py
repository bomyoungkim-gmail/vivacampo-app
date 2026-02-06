import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.domain.entities.aoi import AOI
from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt
from app.domain.value_objects.tenant_id import TenantId


def test_aoi_requires_valid_geometry():
    with pytest.raises(ValidationError):
        AOI(
            tenant_id=TenantId(value=uuid4()),
            farm_id=uuid4(),
            name="Talhao 1",
            use_type="CROP",
            status="ACTIVE",
            geometry_wkt=GeometryWkt(value="POINT (0 0)"),
            area_hectares=AreaHectares(value=10.0),
        )


def test_aoi_update_geometry():
    aoi = AOI(
        tenant_id=TenantId(value=uuid4()),
        farm_id=uuid4(),
        name="Talhao 1",
        use_type="PASTURE",
        status="ACTIVE",
        geometry_wkt=GeometryWkt(value="POLYGON ((0 0, 0 1, 1 1, 0 0))"),
        area_hectares=AreaHectares(value=10.0),
    )

    aoi.update_geometry(
        GeometryWkt(value="MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))"),
        AreaHectares(value=20.0),
    )

    assert aoi.area_hectares.value == 20.0
