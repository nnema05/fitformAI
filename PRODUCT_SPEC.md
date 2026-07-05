# FitForm AI — Product Spec (Complete: Phases 1–5)

> Read this file before writing any code. Do not build anything outside the scope defined here.
> If a request seems to require something not in this spec, stop and ask.

## One sentence
An Apple-native, privacy-first fashion assistant that turns a clothing inspiration image + body info into a personalized, makeable garment plan — and eventually printable patterns and knitting instructions.

## Target user
Creative people who have ideas for clothes but don't know how clothing is made. Not designers, not sewers — normal people who want custom clothing.

## Scope of THIS project (Phases 1–5)
The complete FitForm AI vision, built in phases. Phase 6 (physical robotics) is explicitly OUT for now — the geometry data is shaped so a robot *could* consume it later, but no robot/simulation code is built. Each phase is a shippable increment; earlier phases don't block on later ones.

- **Phase 1 — AI Fashion Generator MVP:** image → garment type + fit + materials + instructions.
- **Phase 2 — Body Scan + Fit:** approximate body measurements → adjust the plan to the user's size.
- **Phase 3 — Pattern Generator:** measurements → real 2D cut pieces (SVG/PDF) for all 4 garment classes.
- **Phase 4 — Knitting Feature:** sweater designs → yarn estimate + knitting instructions / stitch chart.
- **Phase 5 — Robotics Simulation:** simulate (not build) the sewing workflow — fabric layout, arm path, seam detection.

### Why Phase 3 is the pivotal output
Phase 1 + 2 produce a *plan* and a *size* — the "what and how much," not the "cut this shape." Neither a human nor a robot can make a garment from that alone. Phase 3 generates the 2D pattern pieces (front panel, back panel, sleeves) as SVG/PDF: the printable template a person lays on fabric and cuts around, and the geometric data a future sewing robot would consume as coordinates + seam paths.

### Phase 1 — AI Fashion Generator MVP
Upload a design/photo → get garment type, size/fit suggestions, material estimate, and step-by-step making instructions.

Flow:
1. User uploads an inspiration image.
2. MLX classifier predicts garment type (shirt, dress, sweater, pants). **BUILT** — see MLX section.
3. User confirms/edits garment type + fit (tight / regular / loose / oversized).
4. Rule-based engine estimates materials.
5. Cloud LLM generates construction plan.
6. SwiftUI displays the result.

### Phase 2 — Body Scan + Fit Recommendation
User scans body → app estimates APPROXIMATE measurements → adjusts garment plan.

- Approximate measurements ONLY at first. Do not claim precision.
- Use Apple Vision pose detection + user-entered height as calibration.
- Store a measurement profile and connect it to the garment generator.

### Phase 3 — Pattern Generator
Generate actual 2D pattern pieces from garment type + measurements. **Final goal: all 4 garment classes (shirt, dress, sweater, pants). Build ONE first, then expand.**

Flow:
1. Take garment type (Phase 1) + measurement profile (Phase 2).
2. Rule-based geometry engine drafts pattern blocks.
3. Scale pieces to measurements + fit ease.
4. Emit SVG pattern pieces and a printable PDF with a cutting layout.

- **Build order:** get ONE garment (e.g. oversized T-shirt) working end-to-end (measurements → SVG → PDF) to prove the whole pipeline, THEN replicate the drafting logic to the other three classes. Each garment (shirt/dress/sweater/pants) is a separate geometry problem — one-then-expand de-risks it. The target is all four; the sequencing is incremental.
- Rule-based drafting first. An MLX model to predict pattern adjustments is a later refinement, NOT the starting point.
- Human-facing output: printable PDF pattern + cutting layout, for each of the 4 classes.
- Robot-facing output (future-proofing the data shape): each piece as vector coordinates, plus a seam graph describing which edges join which and in what order. Design the geometry data so a robot could later consume it — but do NOT build any robot/simulation code.

### Phase 4 — Knitting Feature
Upload a sweater design → app gives a yarn estimate + knitting instructions / stitch grid. (More realistic than sewing robotics — digital knitting machines already exist.)

Flow:
1. User picks yarn weight, color, gauge, size, fit for a sweater-type garment.
2. Rules estimate yarn amount and needle size from gauge + measurements.
3. Generate panels (front, back, sleeves) as a stitch chart / grid.
4. Export PDF instructions + stitch-chart image.

- Rules first: gauge → yarn amount, size → stitch/row counts per panel.
- Later refinement: MLX/Vision for color-palette extraction and visual pattern recognition from a design image.
- Scope note: knitting applies to knit garments (sweaters); it does not replace the Phase 3 sewing patterns for woven garments.

### Phase 5 — Robotics Simulation (SIMULATE only — do NOT build hardware)
Simulate the sewing workflow to validate the Phase 3 geometry data, without any physical robot.

Flow:
1. Feed Phase 3 pattern pieces (coordinates + seam graph) into a simulation.
2. Simulate fabric-piece locations on a virtual table.
3. Simulate a robotic-arm path following a seam line.
4. Computer vision (simulated) detects fabric edge / seam line; a path planner generates the sewing trajectory.

- Tools: ROS2, Gazebo/Isaac Sim (simulation environments) — later, not required to start.
- This phase consumes the robot-facing data shape from Phase 3; it is where that data proves useful.
- Hard boundary: simulation ONLY. No hardware, no physical robot code. Phase 6 (physical robotics) remains fully out of scope.

## Non-goals (do NOT build)
- No physical robotics / hardware (Phase 6) — Phase 5 is simulation ONLY.
- No precise body measurement claims (Phase 2 is approximate only).
- No user auth/accounts system yet unless trivial.
- No cloud deployment; local dev only for now.
- Within any phase: don't jump ahead to later-phase features; build the current phase's increment first.

## Architecture
- **Frontend:** SwiftUI iOS app (the Apple angle is the point).
- **Backend:** FastAPI (Python).
- **Database:** SQLite via SQLAlchemy ORM. (Chosen over Postgres for simplicity; ORM keeps a future Postgres migration cheap.)
- **Local AI:** MLX for garment image classification (privacy, latency, offline-first). **BUILT** — see below.
- **Rules:** Python functions for fit/material estimates.
- **Cloud LLM:** Generates longer construction instructions only.

### MLX garment classifier — CURRENT STATE (built, working)
Lives in `mlx_model/`. A 4-class classifier (Pants / Sweater / Dress / Shirt), ~0.92 test accuracy on real product photos.
- `garment_model.py` — the `GarmentNet` architecture (784→64→4), shared by training and inference (single source of truth).
- `garment_classifier.py` — training script: loads `ashraq/fashion-product-images-small`, preprocesses (grayscale, resize 28×28, normalize, flatten to 784), trains, imports `GarmentNet` from `garment_model.py`, and saves weights to `garment_model.safetensors`.
- `predict_function.py` — inference module the app calls: imports `GarmentNet`, loads saved weights once, exposes `predict(pil_image) -> {"garment": str, "confidence": float}`. Verified working (returns e.g. `{'garment': 'Shirt', 'confidence': 0.989}`).
- `garment_model.safetensors` — the saved trained weights (the artifact the app loads; don't retrain per request).

Integration contract: the FastAPI `/upload-design` route calls `predict(pil_image)` and returns the garment guess + confidence. Preprocessing at inference MUST match training exactly (same grayscale/resize/normalize). Grayscale is intentional — garment *type* is about shape; color/material are separate concerns (color can be read from pixels or the dataset's `baseColour`; material is user-input or a future model).
Known limits: ~0.92 accuracy plateau (simple net); Shirt/Sweater and Dress/Shirt are the fuzzy boundaries (I merged Tshirts/Sweatshirts into classes). User confirms/edits the guess in the UI, so this accuracy is fine for MVP. Transfer learning is the deferred upgrade if higher accuracy is needed.

### Why MLX / on-device
Users upload personal body photos and original clothing ideas. On-device classification keeps sensitive data private, reduces latency and cloud cost, and works before anything leaves the device. Cloud LLM is used only where long-form generation genuinely helps.

## Data models (SQLAlchemy)
- **Design:** id, image_path, garment_type, fit_preference, created_at
- **Project:** id, design_id (FK), name, status, created_at
- **MeasurementProfile:** id, height, chest, waist, hips, shoulder_width, sleeve_length, inseam, is_approximate (bool), created_at
- **GarmentPlan:** id, project_id (FK), materials_json, instructions_text, confidence, created_at
- **Pattern:** id, project_id (FK), garment_type, pieces_svg_paths_json, seam_graph_json, pdf_path, created_at
- **KnitPlan:** id, project_id (FK), yarn_weight, yarn_amount, needle_size, gauge, panels_json, stitch_chart_path, pdf_path, created_at
- **SimRun:** id, pattern_id (FK), fabric_layout_json, arm_path_json, seam_trajectory_json, created_at  *(Phase 5 — simulation records only)*

## API routes
Phase 1:
- `POST /upload-design` — accept image, return design_id + predicted garment_type
- `POST /generate-plan` — given garment_type, size, fit, material → construction plan
- `POST /estimate-materials` — given garment_type, size, fit → fabric/yarn estimate
- `POST /save-project`
- `GET /project/{id}`

Phase 2:
- `POST /body-scan` — accept pose landmarks + height → approximate measurements
- `POST /fit-adjustment` — adjust garment plan to a measurement profile

Phase 3:
- `POST /generate-pattern` — garment type + measurements + ease → pattern pieces (SVG) + seam graph (all 4 classes)
- `GET /pattern/{id}.pdf` — printable PDF with cutting layout

Phase 4:
- `POST /generate-knit-plan` — sweater design + yarn/gauge/size → yarn estimate + panels + stitch chart
- `GET /knit-plan/{id}.pdf` — PDF instructions + stitch chart

Phase 5 (simulation only):
- `POST /simulate-sew` — take a Pattern's coordinates + seam graph → simulated fabric layout, arm path, seam trajectory
- `GET /sim/{id}` — retrieve a simulation run's results

## Build order (with mock data first at each step)
1. SwiftUI app shell: upload image → fit selector → result screen (mock data).
2. FastAPI skeleton: all routes return mock responses.
3. Rule-based garment planner v1 (real rule logic, PLACEHOLDER numbers, still no ML). `/generate-plan` returns a basic rules plan.
4. Integrate MLX garment classifier. **DONE** — `mlx_model/predict_function.py` exposes `predict(pil_image)`. (Wiring it into `/upload-design` replaces that route's mock garment type.)
5. **Sizing accuracy pass:** replace placeholder numbers in `planner.py` with REAL, cited values from published size charts / pattern envelopes, and add tests that pin outputs to those sources. (See "Sizing accuracy" section below.)
6. **Cloud LLM construction plan (v2 of `/generate-plan`):** upgrade the plan from basic rule steps to rich, natural-language sewing instructions generated by a cloud LLM. Rules still produce the structured data (panels, materials); the LLM turns it into readable step-by-step instructions. Keep the rule-based v1 as a fallback if the LLM call fails.
7. Phase 2: Apple Vision body-pose capture (landmarks only, visualized).
8. Phase 2: approximate measurement estimation from landmarks + height.
9. Connect measurement profile to the generator.
10. Phase 3: pattern drafting for ONE garment (oversized T-shirt block) end-to-end.
11. Phase 3: SVG generation in Python for that one block, sized from measurements + ease.
12. Phase 3: PDF export with cutting layout + preview screen.
13. Phase 3: structure the geometry as coordinates + seam graph (robot-ready data shape).
14. Phase 3: replicate drafting to the other 3 classes (dress, sweater, pants).
15. Phase 4: yarn estimator + stitch-chart generator for sweaters; PDF export.
16. Phase 5: simulate fabric layout + arm path + seam detection from Phase 3 geometry (ROS2/Gazebo/Isaac Sim). Simulation only — no hardware.

## Two forms of `/generate-plan` (rules → LLM)
- **v1 (rules, build step 3):** deterministic, free, no external call. Returns structured panels + simple ordered steps from `planner.py`. Good enough to build and test the whole pipeline.
- **v2 (Cloud LLM, build step 6):** the LLM takes the structured rule output (garment type, panels, materials, fit) and generates rich, natural-language construction instructions. The rules still own the *facts* (what panels, how much fabric); the LLM only makes them *readable*. On LLM failure, fall back to the v1 rule text so the endpoint never hard-fails.

## Sizing accuracy (planned — do NOT block early steps on this)
The concern: I don't know sewing, so how do I trust the numbers? Answer: sizing/fabric data is *published, standardized* information — I source it from real references, I don't invent it. Accuracy becomes a research + testing task, not a sewing-expertise task.
- **Body measurements** (size → chest/waist/hip inches) are well-standardized: encode from a real published size chart, with a source comment on each value.
- **Fabric estimates** are fuzzier (depend on fabric width, style, cut): match published pattern-envelope ranges; tests check *reasonable bounds*, not exact values.
- **Tests as the safety net:** write known-correct examples from a trusted source (e.g. `assert get_measurements("Shirt","Medium")["chest_inches"] == 40  # source: <chart>`). Strict equality for measurements; bounds checks for fabric. The accuracy lives in the cited sources + tests, not in my head.
- **Built-in safety net:** the user confirms/edits the plan (per Phase 1 flow), so estimates are a good starting point, not a claim of authority.
- When to do this: build step 5, AFTER the pipeline works with placeholders. Research the real charts together, encode with citations, then write the tests.

## Definition of a good response from the plan generator
- Names the garment type in plain language.
- Lists materials with quantities and a unit.
- Lists construction steps as an ordered list of panels/actions.
- Includes a confidence score and flags approximations.

## Understanding rule (must hold for every AI-generated change)
For every feature the AI writes, I must be able to answer:
1. What files changed?
2. What does each main function do?
3. How would I test it?
4. What breaks if an input changes?
5. How does this connect to the product vision?
