# JARZ-AI

This repository contains the JARZ-AI project. The repository layout has been organized to separate frontend, backend, and model assets and to document how to run each component.

## Repository layout

Top-level structure
- README.md                  — This file
- .gitignore                 — files to ignore in git
- plan.md                    — project plan and notes
- docs/                      — design, architecture and API docs
- backend/                   — backend service (API, server-side logic)
  - README.md                — how to run and configure the backend
  - .env                     — environment variables (do not commit secrets)
  - src/                     — backend source code
  - requirements.txt / package.json
  - scripts/                 — backend scripts (migrations, start, etc.)
- frontend/                  — frontend application
  - README.md                — how to run and configure the frontend
  - package.json / yarn.lock
  - src/                     — frontend source code
  - public/                  — static public assets
- models/ (or `JARZ-AI/`)    — model code, notebooks, trained model artifacts
  - notebooks/
  - model-files/
- docs/                      — design docs, architecture diagrams, API reference
- tools/ or scripts/         — repo-level scripts (deploy, ci helpers)
- examples/                  — example usage, quick start demos
- tests/                     — integration / e2e tests

Notes:
- Environment variables: The file `env.txt` has been moved to `backend/.env`. The secret contained in `env.txt` has been committed in the repository history — rotate any exposed keys immediately.
- Move or add code: Keep frontend and backend self-contained with their own README and dependency files.
- Large files: Avoid committing large model binaries; use Git LFS or external storage for trained models.

## How to get started (quick)

1. Backend:
   - Move environment variables into `backend/.env` (already created) and do not commit secrets.
   - From `backend/`, follow instructions in `backend/README.md` to install dependencies and run the service.

2. Frontend:
   - From `frontend/`, follow `frontend/README.md` to install and run the frontend.
