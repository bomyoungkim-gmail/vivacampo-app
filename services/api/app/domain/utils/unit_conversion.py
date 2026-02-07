"""Unit conversion helpers."""
from __future__ import annotations


SACK_KG = 60.0  # 1 saca = 60 kg (BR standard)


def to_kg_ha(value: float, unit: str) -> float:
    if unit == "kg_ha":
        return value
    if unit == "sc_ha":
        return value * SACK_KG
    raise ValueError("Unsupported unit")
