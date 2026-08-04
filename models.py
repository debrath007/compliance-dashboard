"""
Pydantic models for the Customer Preference API.

Field set and validation rules intentionally mirror the reference contract in
ComplianceAgent's ``guardrails/engine_a_contract.py`` (KNOWN_COMM_CHANNELS,
DEFAULTS, zip coercion, display_name length cap) so this service is a
realistic Engine A target: unknown enums, bad zips, and oversized names get a
controlled 422 from FastAPI/Pydantic validation rather than an unhandled 500.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

CommChannel = Literal["email", "sms", "push", "mail"]

MAX_DISPLAY_NAME = 128


def _coerce_zip(raw: Optional[object]) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s.lstrip("-").isdigit() or s.startswith("-") or len(s) > 5:
        raise ValueError(f"zip_code invalid: {raw!r}")
    return s.zfill(5)


class PreferenceBase(BaseModel):
    marketing_opt_in: bool = False
    comm_channel: CommChannel = "email"
    zip_code: Optional[str] = None
    display_name: str = Field("", max_length=MAX_DISPLAY_NAME)

    @field_validator("zip_code", mode="before")
    @classmethod
    def validate_zip(cls, v):
        return _coerce_zip(v)


class PreferenceCreate(PreferenceBase):
    customer_id: str = Field(..., min_length=1)


class PreferenceUpdate(BaseModel):
    marketing_opt_in: Optional[bool] = None
    comm_channel: Optional[CommChannel] = None
    zip_code: Optional[str] = None
    display_name: Optional[str] = Field(None, max_length=MAX_DISPLAY_NAME)

    @field_validator("zip_code", mode="before")
    @classmethod
    def validate_zip(cls, v):
        return _coerce_zip(v)


class Preference(PreferenceBase):
    customer_id: str
