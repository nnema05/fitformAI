"""
models.py — Pydantic request/response schemas for FitForm AI Phase 1.

All enums are lowercase on the wire so they're easy to send from Swift without
case-mangling. The API converts to display-case strings before returning them
to the user.
"""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GarmentType(str, Enum):
    shirt   = "shirt"
    dress   = "dress"
    sweater = "sweater"
    pants   = "pants"


class FitPreference(str, Enum):
    tight     = "tight"
    regular   = "regular"
    loose     = "loose"
    oversized = "oversized"


class Size(str, Enum):
    xs  = "XS"
    s   = "S"
    m   = "M"
    l   = "L"
    xl  = "XL"
    xxl = "XXL"


# ---------------------------------------------------------------------------
# /upload-design
# ---------------------------------------------------------------------------

class UploadDesignResponse(BaseModel):
    design_id:    str        = Field(..., description="Opaque ID for this upload (not yet persisted — no DB row created)")
    garment_type: GarmentType = Field(..., description="Garment type predicted by the on-device MLX classifier")
    confidence:   float      = Field(..., description="Classifier softmax confidence for the top class (0.0-1.0)")
    note:         str        = Field(..., description="Human-readable note prompting the user to confirm/edit the prediction")


# ---------------------------------------------------------------------------
# /estimate-materials
# ---------------------------------------------------------------------------

class EstimateMaterialsRequest(BaseModel):
    garment_type:   GarmentType   = Field(..., description="Type of garment to estimate for")
    size:           Size          = Field(..., description="Target garment size")
    fit_preference: FitPreference = Field(..., description="Desired fit")


class MaterialItem(BaseModel):
    name:     str   = Field(..., description="Material name (e.g. 'Cotton fabric')")
    quantity: float = Field(..., description="Numeric quantity")
    unit:     str   = Field(..., description="Unit of measure (e.g. 'm', 'g', 'pcs')")


class EstimateMaterialsResponse(BaseModel):
    garment_type:   GarmentType        = Field(...)
    size:           Size               = Field(...)
    fit_preference: FitPreference      = Field(...)
    materials:      List[MaterialItem] = Field(..., description="Rule-based material estimates")
    # APPROXIMATE: quantities are rule-based estimates, not measured values
    is_approximate: bool               = Field(True, description="Always True — quantities are APPROXIMATE estimates")


# ---------------------------------------------------------------------------
# /generate-plan
# ---------------------------------------------------------------------------

class GeneratePlanRequest(BaseModel):
    garment_type:   GarmentType   = Field(...)
    size:           Size          = Field(...)
    fit_preference: FitPreference = Field(...)
    # Primary material chosen by user or returned from /estimate-materials
    primary_material: str         = Field(..., description="E.g. 'cotton', 'linen', 'denim', 'wool yarn'")


class ConstructionStep(BaseModel):
    step_number: int = Field(...)
    description: str = Field(...)


class GeneratePlanResponse(BaseModel):
    garment_type:     GarmentType          = Field(...)
    size:             Size                 = Field(...)
    fit_preference:   FitPreference        = Field(...)
    primary_material: str                  = Field(...)
    panels:           List[str]            = Field(..., description="Named pattern pieces / panels for this garment")
    steps:            List[ConstructionStep] = Field(..., description="Ordered construction steps")
    # APPROXIMATE: all content is rule-based; LLM-generated instructions come later
    is_approximate: bool = Field(True, description="Always True — rule-based plan only; LLM instructions are build-order step 6")
