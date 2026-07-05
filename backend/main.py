"""
main.py — FitForm AI FastAPI backend, Phase 1 (build-order steps 2–4).

Routes
------
POST /upload-design      — accepts an image file; runs MLX garment classifier.
POST /estimate-materials — rule-based fabric/yarn estimate.
POST /generate-plan      — rule-based construction panels + ordered steps.

Run locally:
    cd backend
    uvicorn main:app --reload --port 8000

Interactive docs: http://localhost:8000/docs
"""

from __future__ import annotations

import uuid
import webbrowser

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from models import (
    EstimateMaterialsRequest,
    EstimateMaterialsResponse,
    FitPreference,
    GarmentType,
    GeneratePlanRequest,
    GeneratePlanResponse,
    Size,
    UploadDesignResponse,
)
from planner import PlanResult, estimate_materials, generate_plan
from classifier import predict_from_bytes

app = FastAPI(
    title="FitForm AI",
    description="Phase 1 backend — rule-based garment planner. No auth, local dev only.",
    version="0.1.0",
)

DOCS_URL = "http://localhost:8000/docs"


@app.on_event("startup")
async def open_docs() -> None:
    """Print the Swagger UI URL on startup and open it in the default browser."""
    print(f"\n  FitForm AI backend running.")
    print(f"  Swagger UI → {DOCS_URL}\n")
    webbrowser.open(DOCS_URL)


# Lowercase classifier output ("Shirt") → GarmentType enum (GarmentType.shirt)
_GARMENT_NAME_MAP: dict[str, GarmentType] = {
    "Shirt":   GarmentType.shirt,
    "Dress":   GarmentType.dress,
    "Sweater": GarmentType.sweater,
    "Pants":   GarmentType.pants,
}


# ---------------------------------------------------------------------------
# POST /upload-design
# ---------------------------------------------------------------------------

@app.post("/upload-design", response_model=UploadDesignResponse)
async def upload_design(file: UploadFile = File(...)) -> UploadDesignResponse:
    """
    Accept a garment inspiration image and return the MLX-predicted garment type.

    The on-device MLX classifier (backend/classifier.py → mlx_model/GarmentNet)
    runs locally — no image data leaves the device. Confidence is the softmax
    probability of the top class (~0.92 average accuracy on the 4-class model).

    The user is expected to confirm or correct the prediction on the next screen
    (FitSelectorScreen in SwiftUI), so ~0.92 accuracy is sufficient for MVP.

    Returns 415 for non-image uploads, 422 for unreadable image data.
    """
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Please upload an image.",
        )

    image_bytes = await file.read()

    try:
        result = predict_from_bytes(image_bytes)
    except ValueError as exc:
        # Unreadable image bytes (corrupt file, wrong extension, etc.)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    garment_type = _GARMENT_NAME_MAP[result["garment"]]
    confidence   = result["confidence"]
    design_id    = f"design-{uuid.uuid4().hex[:8]}"

    return UploadDesignResponse(
        design_id=design_id,
        garment_type=garment_type,
        confidence=confidence,
        note=(
            f"MLX on-device prediction (confidence {confidence:.1%}). "
            "Please confirm or adjust the garment type on the next screen."
        ),
    )


# ---------------------------------------------------------------------------
# POST /estimate-materials
# ---------------------------------------------------------------------------

@app.post("/estimate-materials", response_model=EstimateMaterialsResponse)
def estimate_materials_route(body: EstimateMaterialsRequest) -> EstimateMaterialsResponse:
    """
    Return a rule-based fabric / yarn estimate for the requested garment.

    Logic lives in planner.py. All quantities are APPROXIMATE —
    Phase 3 pattern drafting will produce more accurate per-piece lengths.
    """
    items = estimate_materials(
        garment_type=body.garment_type,
        size=body.size,
        fit=body.fit_preference,
    )
    return EstimateMaterialsResponse(
        garment_type=body.garment_type,
        size=body.size,
        fit_preference=body.fit_preference,
        materials=items,
        is_approximate=True,
    )


# ---------------------------------------------------------------------------
# POST /generate-plan
# ---------------------------------------------------------------------------

@app.post("/generate-plan", response_model=GeneratePlanResponse)
def generate_plan_route(body: GeneratePlanRequest) -> GeneratePlanResponse:
    """
    Return a rule-based garment construction plan.

    Returns the named pattern pieces (panels) and an ordered list of
    construction steps tailored to the garment type, size, fit, and material.

    All content is APPROXIMATE / rule-based. Logic lives in planner.py.
    Build-order step 6 will pass this output to a cloud LLM for richer
    instructions; the rule text remains as a fallback.
    """
    result: PlanResult = generate_plan(
        garment_type=body.garment_type,
        size=body.size,
        fit=body.fit_preference,
        primary_material=body.primary_material,
    )
    return GeneratePlanResponse(
        garment_type=body.garment_type,
        size=body.size,
        fit_preference=body.fit_preference,
        primary_material=body.primary_material,
        panels=result.panels,
        steps=result.steps,
        is_approximate=True,
    )


# ---------------------------------------------------------------------------
# Health check (useful for quick smoke tests)
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    """Returns 200 OK — confirms the server is running."""
    return {"status": "ok", "version": app.version}
