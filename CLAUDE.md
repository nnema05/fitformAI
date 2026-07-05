# CLAUDE.md — FitForm AI

Read `PRODUCT_SPEC.md` before writing any code. Build Phase 1, Phase 2, and Phase 3. Everything in "Non-goals" (knitting, robotics) is off-limits.

## Working style
- Small, reviewable changes. One screen/route/function at a time.
- Mock data first → real rules → ML. Follow the spec's build order.
- After each change, report: files changed, what each function does, how to test it.
- Don't add dependencies, auth, cloud services, or deployment without being asked.
- If something needs to go outside the spec, stop and ask.

## Stack
- SwiftUI (iOS) frontend.
- FastAPI + Pydantic backend.
- SQLite via SQLAlchemy ORM (keep it portable to Postgres later).
- MLX for local garment classification — write wrappers around the model, don't edit model code.
- Cloud LLM only for long-form construction instructions.

## Rule
Every change must leave me able to answer: what changed, what each function does, how to test it, what breaks on bad input, and how it serves the product vision. If I can't, you're building instead of me — slow down.
