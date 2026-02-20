# JOB-HUNTR Implementation Plan

## Overview
A serverless, GitHub-powered job hunting application that allows users to upload their resumes and configure job search preferences. The system uses GitHub Actions as a backend to run Python scrapers and ranking algorithms, committing results back to the repository for the frontend to display.

## Architecture
- **Frontend:** React + Vite (hosted on GitHub Pages).
- **Backend:** GitHub Actions workflow triggered by `repository_dispatch`.
- **Data:** JSON results stored in the repository (e.g., `public/results/<run_id>.json`).

## Phase 1: Project Initialization & Structure
1.  **Initialize Repository:**
    - Create `/home/noah/Development/JOB-HUNTR`.
    - Initialize Git.
    - Structure:
      ```text
      JOB-HUNTR/
      ├── .github/workflows/   # Actions
      ├── backend/             # Python scripts (migrated from job_stuff_2026)
      ├── frontend/            # React App (Vite)
      └── README.md
      ```
2.  **Migrate Logic:**
    - Copy `orchestrate_search.py`, `rank_jobs.py`, and `scripts/` from `job_stuff_2026`.
    - Refactor `rank_jobs.py` to accept dynamic configuration (keywords/penalties) via JSON/CLI args.
    - Ensure scrapers output to `backend/data/<run_id>/`.

## Phase 2: The "Backend" (GitHub Actions)
1.  **Workflow (`hunt.yml`):**
    - Trigger: `repository_dispatch` (allows external API triggers).
    - Steps:
      1. Checkout code.
      2. Set up Python 3.11.
      3. Install dependencies (`playwright`, `pandas`, etc.).
      4. **Input Handling:** Parse `client_payload` (resume keywords, location) -> `config.json`.
      5. **Execution:** `python backend/orchestrate_search.py --config config.json --run-id ${{ client_payload.run_id }}`.
      6. **Commit Results:** Add result JSON to `frontend/public/results/<run_id>.json`.
      7. **Push:** Commit and push to `gh-pages` branch.

## Phase 3: The Frontend (React/Vite)
1.  **Setup:** Initialize Vite + React + TypeScript in `frontend/`.
2.  **UI Components:**
    - **Resume Input:** Text area or file picker (pdf.js/mammoth.js for local parsing).
    - **Preferences:** Inputs for Job Titles, Location, Blacklisted Keywords.
    - **"HUNT" Button:**
      - Generates UUID (`run_id`).
      - Calls `POST https://api.github.com/repos/noahoosting/JOB-HUNTR/dispatches`.
      - *Note: Requires a limited-scope PAT or proxy for friends.*
3.  **Polling Logic:**
    - Show "Hunting..." loading state.
    - Poll `https://noahoosting.github.io/JOB-HUNTR/results/<run_id>.json` every 30s.
    - Render ranked job list on success (200 OK).

## Phase 4: Polishing & Deployment
1.  **Results Dashboard:** Sortable table (TanStack Table).
2.  **Filters:** Match Score, Source, etc.
3.  **Deployment:** Configure repo to deploy `frontend/dist` to GitHub Pages.

