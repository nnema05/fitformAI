# Copilot Instructions — FitForm AI

## Before doing anything
Read `PRODUCT_SPEC.md` in the repo root. Do not build anything outside its scope.
We are building Phase 1, Phase 2, and Phase 3 (pattern generation). Knitting and robotics are out of scope.
Phase 3 is the real deliverable — it produces the printable pattern pieces a human cuts, plus geometry structured so a future robot could consume it. Do not build robot/simulation code.

## How I want you to work
- Work in small, reviewable increments. One screen, one route, or one function at a time.
- Prefer mock data first, then real logic, then ML. Follow the build order in the spec.
- Explain assumptions in code comments, especially for any measurement or material math.
- When you finish a change, tell me: what files changed, what each main function does, and how to test it.
- Do not add dependencies, cloud services, auth, or deployment config unless I ask.
- If a request seems to need something outside the spec, stop and ask instead of guessing.

## Tech constraints
- Frontend: SwiftUI (iOS).
- Backend: FastAPI (Python), Pydantic models.
- Database: SQLite via SQLAlchemy ORM. No Postgres yet, but keep code ORM-portable.
- Local ML: MLX for garment classification. Don't modify model code unless asked; write inference wrappers around it.
- Cloud LLM: only for long-form construction instructions.

## Style
- Keep code simple and modular. Small functions, clear names.
- No premature abstraction. Favor readability over cleverness.
- Mark all Phase 2 body measurements as APPROXIMATE in both code and UI.
