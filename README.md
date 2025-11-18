# Personalized Fitness Nutrition Planner - v2 (Option B: Professional Fitness Theme)

This upgraded project is an attractive, multi-feature web application built for your evaluation.
Theme: Sporty dark (black / neon green/orange) — Option B.

## Features
- Modern, sporty UI (dark theme, hero banner, images)
- Authentication (signup/login) with password hashing
- Dashboard with charts (Chart.js via CDN)
- Workouts, Diet entries, Progress tracking
- Wearable data manual input page
- AI-like recommendation engine (simple rule-based)
- Community: points, badges, leaderboard
- MySQL-compatible SQL dump and SQLite fallback (zero setup)
- .env support (see .env.example)

## Quick run (SQLite demo)
1. Extract ZIP.
2. Create virtualenv and activate.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` (optional) or rely on defaults.
5. Run:
   ```
   python app.py
   ```
6. Open http://127.0.0.1:5000

Demo credentials:
- email: demo@demo.com
- password: DemoPass123

## Using MySQL
- Set USE_MYSQL=true in `.env` and provide MYSQL_* variables.
- Import `sql/sample_db_mysql.sql` into your MySQL server.
- Restart app.

## Notes
- Charts use Chart.js from CDN (no extra install).
- Recommendation engine is simple and explainable — good for demo.
- If you want a PPT/report, tell me and I'll add it.

Good luck with your evaluation — I can also customize colors, add logos, or generate the presentation slides now if you want.
