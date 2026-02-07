from unittest.mock import MagicMock

import pytest

from app.infrastructure.adapters.persistence.sqlalchemy.aoi_repository import SQLAlchemyAOIRepository


def _repo_with_row(row):
    repo = SQLAlchemyAOIRepository(MagicMock())
    repo._execute_query = MagicMock(return_value=row)
    return repo


def test_normalize_geometry_rejects_empty():
    repo = _repo_with_row(
        {
            "geometry": None,
            "area_ha": None,
            "is_valid": True,
            "is_empty": True,
            "reason": "Empty geometry",
        }
    )
    with pytest.raises(ValueError, match="valid MultiPolygon"):
        repo._normalize_geometry("MULTIPOLYGON EMPTY")


def test_normalize_geometry_rejects_invalid():
    repo = _repo_with_row(
        {
            "geometry": None,
            "area_ha": None,
            "is_valid": False,
            "is_empty": False,
            "reason": "Self-intersection",
        }
    )
    with pytest.raises(ValueError, match="Invalid geometry"):
        repo._normalize_geometry("MULTIPOLYGON ((...))")


def test_normalize_geometry_accepts_valid():
    repo = _repo_with_row(
        {
            "geometry": "MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))",
            "area_ha": 12.34,
            "is_valid": True,
            "is_empty": False,
            "reason": "Valid Geometry",
        }
    )
    geometry, area = repo._normalize_geometry("MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))")
    assert geometry.startswith("MULTIPOLYGON")
    assert area == 12.34
