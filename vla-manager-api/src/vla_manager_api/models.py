"""Pydantic v2 schemas accepted/returned by the VLA Manager API.

These mirror the Kotlin DTOs byte-for-byte so the existing VLA Manager
Vue UI and consumers of the prior ``dva-api /vla`` routes interoperate
without contract changes.

Reference:
- model/src/main/kotlin/hu/bme/mit/ftsrg/dva/vla/VLANew.kt
- model/src/main/kotlin/hu/bme/mit/ftsrg/odcs/DataQuality.kt
- model/src/main/kotlin/hu/bme/mit/ftsrg/dva/dto/IDDTO.kt
- model/src/main/kotlin/hu/bme/mit/ftsrg/dva/dto/ErrDTO.kt
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DataQuality(BaseModel):
    """A single quality requirement (ODCS DataQuality fragment)."""

    engine: str
    implementation: str


class VLANew(BaseModel):
    """Body of ``POST /vla``. All fields optional — partial ODCS payload.

    The ``schema`` field is renamed via alias because ``schema`` is a
    reserved attribute name on pydantic BaseModel. Inputs and outputs
    use the JSON key ``schema`` transparently.
    """

    model_config = ConfigDict(populate_by_name=True)

    description: Optional[str] = None
    servers: Optional[list[Any]] = None
    schema_: Optional[dict[str, Any]] = Field(default=None, alias="schema")
    quality: Optional[list[DataQuality]] = None
    price: Optional[dict[str, Any]] = None
    team: Optional[list[Any]] = None
    roles: Optional[list[Any]] = None
    slaProperties: Optional[list[Any]] = None
    support: Optional[list[Any]] = None
    tags: Optional[list[Any]] = None


class IDDTO(BaseModel):
    id: UUID


class ErrDTO(BaseModel):
    type: str
    title: str