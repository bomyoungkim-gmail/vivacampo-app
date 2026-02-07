"""Property-based tests for domain value objects."""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt
from app.domain.value_objects.tenant_id import TenantId


@st.composite
def polygon_wkt(draw) -> str:
    coords = draw(
        st.lists(
            st.tuples(
                st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False),
                st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False),
            ),
            min_size=4,
            max_size=4,
        )
    )
    closed = coords + [coords[0]]
    points = ", ".join([f"{x} {y}" for x, y in closed])
    prefix = draw(st.sampled_from(["POLYGON", "MULTIPOLYGON"]))
    if prefix == "POLYGON":
        return f"POLYGON (({points}))"
    return f"MULTIPOLYGON ((({points})))"


@given(st.floats(min_value=1e-6, max_value=10000, allow_nan=False, allow_infinity=False))
def test_area_hectares_accepts_valid_values(value: float) -> None:
    obj = AreaHectares(value=value)
    assert obj.value == value


@given(
    st.one_of(
        st.floats(max_value=0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=10000.000001, max_value=1e9, allow_nan=False, allow_infinity=False),
    )
)
def test_area_hectares_rejects_invalid_values(value: float) -> None:
    with pytest.raises(ValueError):
        AreaHectares(value=value)


@given(polygon_wkt())
def test_geometry_wkt_accepts_polygon(value: str) -> None:
    obj = GeometryWkt(value=value)
    assert obj.value == value


@given(st.text(min_size=1))
def test_geometry_wkt_rejects_non_polygon(value: str) -> None:
    if value.startswith("POLYGON") or value.startswith("MULTIPOLYGON"):
        return
    with pytest.raises(ValueError):
        GeometryWkt(value=value)


@given(st.uuids())
def test_tenant_id_accepts_uuid(value) -> None:
    obj = TenantId(value=value)
    assert obj.value == value
