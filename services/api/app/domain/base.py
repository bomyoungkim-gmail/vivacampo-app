"""
Base classes para dominio com Pydantic (validacao estrita).
"""
from pydantic import BaseModel, ConfigDict


class DomainEntity(BaseModel):
    """Base class para entidades de dominio mutaveis."""

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        frozen=False,
        strict=True,
        arbitrary_types_allowed=False,
    )


class ImmutableDTO(BaseModel):
    """Base class para DTOs imutaveis (Commands/Responses)."""

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        frozen=True,
        strict=True,
        arbitrary_types_allowed=False,
    )


class ValueObject(BaseModel):
    """Base class para value objects imutaveis."""

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        frozen=True,
        strict=True,
        arbitrary_types_allowed=False,
    )
