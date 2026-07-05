"""
classifier.py — Backend wrapper for the MLX garment classifier.

Why this exists instead of importing predict_function.py directly:
  predict_function.py runs `load_dataset(...)` at module level (test/dev code),
  which would trigger a Hugging Face dataset download every time the server starts.
  Per the spec: "write inference wrappers around it, don't edit model code."
  This wrapper imports only GarmentNet (the architecture, the single source of
  truth in garment_model.py) and replicates the identical preprocessing so
  inference output is byte-for-byte the same as predict_function.predict().

Integration contract (from PRODUCT_SPEC.md):
  Preprocessing at inference MUST match training exactly:
    grayscale → resize 28×28 → normalize to [0,1] → flatten to 784 → MLX array
  This matches garment_classifier.py (training) and predict_function.py (reference).

The model is loaded once at import time (not per request).
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import mlx.core as mx
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Path setup — add mlx_model/ to sys.path so GarmentNet can be imported,
# and build an absolute path to the weights file so load_weights() works
# regardless of the server's working directory.
# ---------------------------------------------------------------------------
_MLX_DIR = Path(__file__).resolve().parent.parent / "mlx_model"
if str(_MLX_DIR) not in sys.path:
    sys.path.insert(0, str(_MLX_DIR))

from garment_model import GarmentNet  # noqa: E402 — must come after path setup

_WEIGHTS_PATH = str(_MLX_DIR / "garment_model.safetensors")

# Class order must match training in garment_classifier.py.
# Verified against predict_function.py: ["Pants", "Sweater", "Dress", "Shirt"]
_CLASS_NAMES = ["Pants", "Sweater", "Dress", "Shirt"]

# ---------------------------------------------------------------------------
# Load model once — weights are frozen; no retraining here.
# ---------------------------------------------------------------------------
_model = GarmentNet()
_model.load_weights(_WEIGHTS_PATH)
mx.eval(_model.parameters())  # force weights to materialise in memory


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def predict_from_bytes(image_bytes: bytes) -> dict[str, object]:
    """
    Run the MLX garment classifier on raw image bytes.

    Preprocessing pipeline (must match training in garment_classifier.py):
      1. Decode bytes → PIL Image
      2. Convert to grayscale  (shape/silhouette, not colour, determines garment type)
      3. Resize to 28×28
      4. Normalise pixels to [0, 1]
      5. Flatten to 784-element vector
      6. Add batch dimension → shape (1, 784)

    Returns:
        {"garment": str, "confidence": float}
        where garment is one of "Pants", "Sweater", "Dress", "Shirt"
        and confidence is the softmax probability of the top class.

    Raises:
        ValueError  — if image_bytes cannot be decoded as an image.
        RuntimeError — if MLX inference fails unexpectedly.
    """
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        raise ValueError(f"Could not decode image: {exc}") from exc

    # Preprocessing — identical to predict_function.py and garment_classifier.py
    img = pil_image.convert("L").resize((28, 28))
    arr = (np.array(img, dtype=np.float32) / 255.0).flatten()
    x = mx.array(arr)[None, :]          # shape (1, 784)

    logits = _model(x)                  # shape (1, 4)
    probs = mx.softmax(logits, axis=1)  # probabilities sum to 1
    idx = int(mx.argmax(probs, axis=1).item())
    confidence = float(probs[0, idx].item())

    return {
        "garment": _CLASS_NAMES[idx],
        "confidence": round(confidence, 3),
    }
