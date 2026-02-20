# 🛡️ JOB-HUNTR

A serverless, GitHub-powered job hunting application.

## How it works
1. **Frontend:** A React app hosted on GitHub Pages.
2. **Backend:** GitHub Actions runs Python scrapers and ranking algorithms.
3. **Data:** Results are committed back to the repository as JSON files and displayed by the frontend.

## Components
- `.github/workflows/hunt.yml`: The engine that runs the search.
- `backend/`: Python scripts for scraping (LinkedIn, Indeed, HN, etc.) and ranking.
- `frontend/`: Vite + React UI for triggering hunts and viewing results.

## Getting Started
1. Deploy the frontend to GitHub Pages.
2. Generate a GitHub Personal Access Token (PAT) with `repo` scope.
3. Open the JOB-HUNTR UI, enter your search keywords and PAT, and click **START HUNT**.
4. Wait a few minutes for the GitHub Action to finish and results to appear!

## Architecture
- **Trigger:** `repository_dispatch` (event: `hunt`)
- **Storage:** JSON results in `frontend/public/results/`
- **Ranking:** Keyword-based scoring system in `backend/rank_jobs.py`
