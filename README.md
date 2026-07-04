# Multi Agent Mentor 🧭

A simple, fully local, multi-agent career mentoring web app. **No external API keys, no cloud services** — everything runs on your machine with a rule-based "AI" engine and a local SQLite database.

## Features

1. **Dashboard** — snapshot of your assessments, resume score, roadmap progress and chat activity
2. **Career Assessment Agent** — 7-question quiz that matches you to 10 careers using a trait-similarity scoring model
3. **Learning Roadmap Agent** — generates a step-by-step checklist for any supported career; check off topics as you go
4. **Resume Review Agent** — paste your resume text and get an instant heuristic score (0–100) with actionable feedback
5. **Career Chat Agent** — rule-based chatbot that answers questions about resumes, interviews, skills, salaries, and transitions
6. **Job Recommendation Agent** — suggests job titles matched to a career track and your listed skills
7. **Profile** — view/edit your account name and bio

## Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, SQLite, PyJWT (auth)
- **Frontend:** Plain HTML/CSS/JavaScript (no build step, no npm required) — served as static files
- **AI Engine:** 100% local, rule-based heuristics (trait scoring, keyword matching) — zero external API calls


- The backend runs on port **5000**, the frontend expects it at `http://127.0.0.1:5000` (see `API_BASE` at the top of `frontend/app.js` if you need to change the port).
- Everything is stored locally in `backend/careerpilot.db`. Delete this file any time to reset all data.
- This app intentionally has **no external AI API dependency** — all "agent" logic (career matching, resume scoring, chat replies, job matching) is implemented with transparent, inspectable rules in `career_data.py` and `app.py`.
