"""
planner.py — Rule-based garment planner for FitForm AI Phase 1.

Exposes two plain functions that can be imported and tested without starting
the FastAPI server:

    estimate_materials(garment_type, size, fit) -> List[MaterialItem]
    generate_plan(garment_type, size, fit, primary_material) -> PlanResult

Design decisions
----------------
* All rule data lives in plain dicts at module level — easy to read, easy to
  replace with cited values in build-order step 5 (sizing accuracy pass).
* Size and fit effects are kept independent:
    final_fabric = BASE_FABRIC[garment] * SIZE_FACTOR[size] + FIT_EASE[fit]
  This makes it obvious what each variable contributes and simple to unit-test.
* Yarn (sweater) uses grams; woven garments use metres. Units are explicit in
  every MaterialItem so callers never have to guess.
* Steps are phrased for a complete beginner — short, imperative sentences.
  The cloud LLM (build-order step 6) will expand these into richer prose;
  the rule list is the structured scaffold it will refine.

All quantities are APPROXIMATE placeholders. Build-order step 5 will replace
them with values sourced from published size charts / pattern envelopes and
pin them with tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from models import (
    ConstructionStep,
    FitPreference,
    GarmentType,
    MaterialItem,
    Size,
)


# ---------------------------------------------------------------------------
# Rule tables — all values are APPROXIMATE placeholders.
# Source comments will be added in build-order step 5 (sizing accuracy pass).
# ---------------------------------------------------------------------------

# Base fabric (metres) or yarn (grams) for size M / regular fit.
# Woven garments: assumes 150 cm wide fabric, standard cut (no lining).
# Sweater: assumes worsted-weight yarn (~200 m / 100 g).
BASE_FABRIC: dict[GarmentType, float] = {
    GarmentType.shirt:   1.6,   # front + back + 2 sleeves, approx
    GarmentType.dress:   2.4,   # longer body + skirt panel
    GarmentType.sweater: 380.0, # grams of yarn — front + back + 2 sleeves
    GarmentType.pants:   1.9,   # 2 legs + waistband + pockets
}

# Multiplicative size factor relative to M = 1.0.
# Each step is ~9–11 %, a rough approximation of how shell fabric scales with
# body circumference increases. Placeholder — step 5 will use published charts.
SIZE_FACTOR: dict[Size, float] = {
    Size.xs:  0.82,
    Size.s:   0.91,
    Size.m:   1.00,
    Size.l:   1.10,
    Size.xl:  1.21,
    Size.xxl: 1.33,
}

# Additive fit ease: extra metres (woven) or grams (yarn) on top of the
# size-scaled base. Tight removes fabric; oversized adds a meaningful chunk.
# Placeholder — will be refined per-garment in step 5.
FIT_EASE_WOVEN: dict[FitPreference, float] = {
    FitPreference.tight:     -0.10,
    FitPreference.regular:    0.00,
    FitPreference.loose:      0.20,
    FitPreference.oversized:  0.40,
}

FIT_EASE_YARN: dict[FitPreference, float] = {
    FitPreference.tight:     -20.0,
    FitPreference.regular:    0.0,
    FitPreference.loose:      30.0,
    FitPreference.oversized:  60.0,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _scale_fabric(base: float, size: Size, fit: FitPreference) -> float:
    """Scale a woven-fabric base (metres) by size factor + fit ease. Min 0.5 m."""
    return round(max(base * SIZE_FACTOR[size] + FIT_EASE_WOVEN[fit], 0.5), 2)


def _scale_yarn(base: float, size: Size, fit: FitPreference) -> float:
    """Scale a yarn base (grams) by size factor + fit ease. Min 50 g, rounded to 10 g."""
    raw = base * SIZE_FACTOR[size] + FIT_EASE_YARN[fit]
    return round(max(raw, 50.0) / 10) * 10


def _steps(descriptions: List[str]) -> List[ConstructionStep]:
    """Number a flat list of step strings into ConstructionStep objects."""
    return [ConstructionStep(step_number=i + 1, description=d) for i, d in enumerate(descriptions)]


# ---------------------------------------------------------------------------
# Per-garment material lists
# ---------------------------------------------------------------------------

def _shirt_materials(size: Size, fit: FitPreference) -> List[MaterialItem]:
    fabric = _scale_fabric(BASE_FABRIC[GarmentType.shirt], size, fit)
    return [
        MaterialItem(name="Woven fabric (e.g. cotton, linen)", quantity=fabric, unit="m"),
        MaterialItem(name="Matching thread",                   quantity=2,      unit="spools"),
        MaterialItem(name="Buttons",                           quantity=7,      unit="pcs"),
        MaterialItem(name="Interfacing (collar / cuffs)",      quantity=0.4,    unit="m"),
    ]


def _dress_materials(size: Size, fit: FitPreference) -> List[MaterialItem]:
    fabric = _scale_fabric(BASE_FABRIC[GarmentType.dress], size, fit)
    return [
        MaterialItem(name="Woven fabric (e.g. linen, crepe)",  quantity=fabric, unit="m"),
        MaterialItem(name="Matching thread",                   quantity=2,      unit="spools"),
        MaterialItem(name="Invisible zip (55 cm)",             quantity=1,      unit="pcs"),
        MaterialItem(name="Interfacing (neckline facing)",     quantity=0.3,    unit="m"),
    ]


def _sweater_materials(size: Size, fit: FitPreference) -> List[MaterialItem]:
    yarn = _scale_yarn(BASE_FABRIC[GarmentType.sweater], size, fit)
    return [
        MaterialItem(name="Yarn (worsted weight recommended)", quantity=yarn,   unit="g"),
        MaterialItem(name="Knitting needles (4–5 mm)",         quantity=1,      unit="pair"),
        MaterialItem(name="Stitch markers",                    quantity=8,      unit="pcs"),
        MaterialItem(name="Tapestry needle (seaming)",         quantity=1,      unit="pcs"),
    ]


def _pants_materials(size: Size, fit: FitPreference) -> List[MaterialItem]:
    fabric = _scale_fabric(BASE_FABRIC[GarmentType.pants], size, fit)
    return [
        MaterialItem(name="Woven fabric (e.g. denim, chino)",  quantity=fabric, unit="m"),
        MaterialItem(name="Matching thread",                   quantity=2,      unit="spools"),
        MaterialItem(name="Zip (18 cm)",                       quantity=1,      unit="pcs"),
        MaterialItem(name="Waistband elastic or facing",       quantity=0.9,    unit="m"),
        MaterialItem(name="Interfacing (waistband)",           quantity=0.3,    unit="m"),
    ]


# ---------------------------------------------------------------------------
# Per-garment panel + step definitions
# ---------------------------------------------------------------------------

def _shirt_plan(fit: FitPreference, material: str):
    panels = [
        "Front body",
        "Back body",
        "Left sleeve",
        "Right sleeve",
        "Collar",
        "Cuffs (×2)",
    ]
    # Ease note in step 1 makes the fit choice visible in the instructions.
    ease = {
        FitPreference.tight:     "minimal ease (~0 cm at chest)",
        FitPreference.regular:   "standard ease (~5 cm at chest)",
        FitPreference.loose:     "relaxed ease (~10 cm at chest)",
        FitPreference.oversized: "generous ease (~18 cm at chest)",
    }[fit]
    steps = [
        f"Cut front and back body panels from {material} with {ease}.",
        "Staystitch neckline and armhole curves on both panels to prevent stretching.",
        "Sew front to back at shoulder seams; press seams open.",
        "Interface collar piece; fold, press, and stitch to neckline edge.",
        "Mark sleeve caps; ease each sleeve into armhole, pin, then sew.",
        "Sew side seams and sleeve underarm seams in one continuous pass.",
        "Interface cuff pieces; fold and press. Sew cuffs to sleeve ends.",
        "Turn under front placket allowance; press and topstitch both sides.",
        "Sew buttonholes on right front placket; attach buttons to left front.",
        "Press the finished garment thoroughly before fitting.",
    ]
    return panels, _steps(steps)


def _dress_plan(fit: FitPreference, material: str):
    panels = [
        "Front bodice",
        "Back bodice",
        "Front skirt",
        "Back skirt",
        "Neckline facing (×2)",
    ]
    ease = {
        FitPreference.tight:     "fitted (0–2 cm ease at bust)",
        FitPreference.regular:   "standard (4–6 cm ease at bust)",
        FitPreference.loose:     "relaxed (8–10 cm ease at bust)",
        FitPreference.oversized: "oversized (14+ cm ease at bust)",
    }[fit]
    steps = [
        f"Cut bodice and skirt panels from {material} — {ease}.",
        "Staystitch neckline and armhole curves on both bodice panels.",
        "Sew bodice front to back at shoulder seams; press open.",
        "Interface neckline facings; sew facing seams, press, stitch to neckline. Grade and clip seam allowances.",
        "Sew bodice side seams; press open.",
        "Sew skirt front to back at side seams; press open.",
        "Stay-stitch skirt waist edge. Join bodice to skirt at waistline seam, matching notches.",
        "Install invisible zip at centre-back seam from neckline to below waist.",
        "Stitch centre-back seam below zip; press seam open.",
        "Fold and press hem allowance; slip-stitch or machine-stitch hem.",
        "Press finished dress and check fit on a dress form or fitting.",
    ]
    return panels, _steps(steps)


def _sweater_plan(fit: FitPreference, material: str):
    panels = [
        "Back panel",
        "Front panel",
        "Left sleeve",
        "Right sleeve",
        "Neckband",
        "Cuffs (×2)",
    ]
    gauge_note = {
        FitPreference.tight:     "Use the tighter end of your gauge swatch for a snug result.",
        FitPreference.regular:   "Match gauge swatch exactly for standard fit.",
        FitPreference.loose:     "Go up half a needle size from gauge for added drape.",
        FitPreference.oversized: "Go up a full needle size and add 8–10 extra stitches at cast-on.",
    }[fit]
    steps = [
        f"Knit a tension swatch with your {material}; measure carefully. {gauge_note}",
        "Cast on stitches for back panel based on gauge and finished bust measurement.",
        "Work in chosen stitch pattern to underarm, then shape armhole.",
        "Knit back shoulders; place centre-back stitches on a holder for the neckband.",
        "Knit front panel identically up to neckline shaping; work front neck decreases.",
        "Join front to back at shoulders using three-needle cast-off for a clean seam.",
        "Cast on sleeve stitches; work each sleeve with gradual side increases to sleeve-cap.",
        "Sew or graft sleeve caps into armholes; seam sleeve underarm edges.",
        "Pick up neckband stitches; work 2×2 rib for 2–3 cm; cast off loosely.",
        "Block finished sweater to measurements — wet or steam block depending on fibre.",
    ]
    return panels, _steps(steps)


def _pants_plan(fit: FitPreference, material: str):
    panels = [
        "Front leg (×2)",
        "Back leg (×2)",
        "Waistband",
        "Front fly facing",
        "Pocket bags (×4, optional)",
    ]
    ease = {
        FitPreference.tight:     "slim (0–1 cm ease at hip)",
        FitPreference.regular:   "straight (3–5 cm ease at hip)",
        FitPreference.loose:     "relaxed (7–10 cm ease at hip)",
        FitPreference.oversized: "wide-leg (12+ cm ease at hip)",
    }[fit]
    steps = [
        f"Cut front and back leg pieces from {material} — {ease}.",
        "Sew front and back crotch curves separately; clip curves and press.",
        "If including pockets: sew pocket bags to front leg pieces before joining seams.",
        "Stitch front legs together at centre-front seam, leaving zip opening.",
        "Install zip at centre-front; topstitch fly shield.",
        "Sew back legs together at centre-back seam.",
        "Join front unit to back unit at side seams; press seams open.",
        "Sew inner leg seams (both legs) in one continuous pass; clip crotch.",
        "Interface and fold waistband; attach to waist edge. Add button and buttonhole.",
        "Fold hem allowance at each leg; press and stitch to desired length.",
        "Press finished pants, paying attention to centre-front crease if desired.",
    ]
    return panels, _steps(steps)


# ---------------------------------------------------------------------------
# Public API — these two functions are what main.py (and tests) call directly
# ---------------------------------------------------------------------------

def estimate_materials(
    garment_type: GarmentType,
    size: Size,
    fit: FitPreference,
) -> List[MaterialItem]:
    """
    Return a rule-based list of MaterialItems for the given garment, size, and fit.

    Uses BASE_FABRIC * SIZE_FACTOR + FIT_EASE to produce scaled quantities.
    All values are APPROXIMATE — step 5 (sizing accuracy pass) will replace
    them with values sourced from published size charts / pattern envelopes.

    Raises ValueError for an unrecognised garment_type (should never happen
    with valid Pydantic input, but useful as a unit-test guard).
    """
    dispatch = {
        GarmentType.shirt:   _shirt_materials,
        GarmentType.dress:   _dress_materials,
        GarmentType.sweater: _sweater_materials,
        GarmentType.pants:   _pants_materials,
    }
    if garment_type not in dispatch:
        raise ValueError(f"Unknown garment_type: {garment_type!r}")
    return dispatch[garment_type](size, fit)


@dataclass
class PlanResult:
    """Return type of generate_plan — keeps the two outputs together cleanly."""
    panels: List[str]
    steps:  List[ConstructionStep]


def generate_plan(
    garment_type: GarmentType,
    size: Size,
    fit: FitPreference,
    primary_material: str,
) -> PlanResult:
    """
    Return the named pattern pieces (panels) and ordered construction steps
    for the given garment, sized and fit as requested.

    Steps are phrased for a beginner. primary_material is woven into step 1
    so the instructions name the fabric the maker will actually use.

    Size is accepted but not yet reflected in step text — Phase 3 pattern
    drafting will add precise cut dimensions per size.

    All content is APPROXIMATE / rule-based. Build-order step 6 will pass
    this output to a cloud LLM to generate richer, natural-language instructions
    while keeping the rule text as a fallback.

    Raises ValueError for an unrecognised garment_type.
    """
    dispatch = {
        GarmentType.shirt:   _shirt_plan,
        GarmentType.dress:   _dress_plan,
        GarmentType.sweater: _sweater_plan,
        GarmentType.pants:   _pants_plan,
    }
    if garment_type not in dispatch:
        raise ValueError(f"Unknown garment_type: {garment_type!r}")
    panels, steps = dispatch[garment_type](fit, primary_material)
    return PlanResult(panels=panels, steps=steps)
