# FitForm AI

An Apple-native, privacy-first fashion assistant that turns a clothing inspiration image + body info into a personalized, makeable garment plan — and eventually printable patterns and knitting instructions.

Full product scope, phase breakdown, and design rationale live in [`PRODUCT_SPEC.md`](PRODUCT_SPEC.md) — read that first.

## Status

Phase 1 (AI Fashion Generator MVP), build-order steps 1–4, working end-to-end:

- SwiftUI app: Upload → Fit/Size Selector → Result, calling the real backend (no mock data).
- FastAPI backend: `/upload-design`, `/estimate-materials`, `/generate-plan` — rule-based planner, real responses.
- MLX garment classifier: on-device 4-class model (Pants / Sweater / Dress / Shirt), ~0.92 test accuracy, wired into `/upload-design`.

Not yet built: sizing-accuracy pass (real published measurement charts), cloud-LLM instructions (v2 of `/generate-plan`), Phase 2 body scan, Phase 3 pattern generator, Phase 4 knitting, Phase 5 sim. See `PRODUCT_SPEC.md`'s build order for the full sequence.

## Stack

- **Frontend:** SwiftUI (iOS)
- **Backend:** FastAPI + Pydantic
- **Local AI:** MLX (on-device garment classification)
- **Database:** SQLite via SQLAlchemy ORM (planned, not yet wired)
- **Cloud LLM:** planned for long-form construction instructions only

## Repo layout

```
backend/       FastAPI app — routes, Pydantic schemas, rule-based planner, MLX wrapper
mlx_model/     Trained garment classifier (architecture, weights, training script)
FitForm/       SwiftUI iOS app (Xcode project)
PRODUCT_SPEC.md   Full product spec — read before changing anything
```

## Running it locally

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Swagger docs open automatically at `http://localhost:8000/docs`.

### iOS app

Open `FitForm/FitForm.xcodeproj` in Xcode and run on a simulator or device. The app talks to `http://127.0.0.1:8000` (see `APIClient.swift`) — the backend must be running first. On a physical device, `localhost` refers to the device itself, so point `APIClient.baseURL` at your Mac's LAN IP instead.

