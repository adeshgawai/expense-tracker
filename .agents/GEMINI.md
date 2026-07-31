# Spendly — Expense Tracker

A lightweight, modern personal finance tracking application built with Python and Flask.

---

## 🛠️ Tech Stack & Dependencies

- **Language & Runtime**: Python >= 3.13
- **Web Framework**: Flask 3.1.3 (`werkzeug` 3.1.6)
- **Database**: SQLite3 (managed via `database/db.py`)
- **Testing**: Pytest 8.3.5, `pytest-flask` 1.3.0
- **Package Management**: `uv` (`pyproject.toml` & `uv.lock`) or `pip` (`requirements.txt`)
- **Frontend Architecture**:
  - **HTML**: Jinja2 HTML templates extending a shared `base.html` layout
  - **CSS**: Custom Vanilla CSS system (`static/css/style.css`) with CSS custom properties (variables)
  - **JS**: Vanilla JavaScript (`static/js/main.js` and inline page scripts) — no external JS libraries or frameworks

---

## 📁 Repository Structure

```
expense-tracker/
├── app.py              # Main Flask application and route definitions
├── main.py             # Entry point / utility script
├── pyproject.toml      # Project configuration and uv dependencies
├── requirements.txt    # Frozen Python dependencies list
├── uv.lock             # Lockfile for reproducible builds
├── database/
│   ├── __init__.py
│   └── db.py           # SQLite connection helper (get_db), init_db, seed_db
├── static/
│   ├── css/
│   │   └── style.css   # Main stylesheet (design system, variables, layouts)
│   └── js/
│       └── main.js     # Global client-side interactions
└── templates/
    ├── base.html       # Global layout template (navbar, footer, assets)
    ├── landing.html    # Home page with hero, features, and video modal
    ├── login.html      # Authentication sign-in form
    ├── register.html   # Account registration form
    ├── terms.html      # Terms & Conditions legal page
    └── privacy.html    # Privacy Policy legal page
```

---

## 🚀 Build & Run Commands

### Setup & Environment
```bash
# Using uv (Recommended)
uv sync

# Or using standard venv & pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running Locally
```bash
python app.py
```
*Server starts on `http://127.0.0.1:5001` with debug mode enabled.*

### Running Tests
```bash
pytest
```

---

## 📐 Code Style & Conventions

### Python (Flask)
- Follow **PEP 8** style conventions (4-space indentation, snake_case function/variable names).
- Group routes logically and specify standard HTTP methods explicitly when applicable.
- Return responses using `render_template` for HTML pages or JSON/redirects as appropriate.
- Keep database operations cleanly isolated within `database/db.py` functions using parameterized queries to prevent SQL injection.

### Templates & HTML
- Use Jinja template inheritance (`{% extends "base.html" %}`).
- Write semantic HTML5 elements (`<nav>`, `<header>`, `<main>`, `<section>`, `<footer>`, `<ul>`, `<li>`).
- Include accessibility attributes (e.g., `aria-label`, `role`, `aria-hidden`, keyboard navigation handlers).
- Keep content accessible and standard compliant (e.g., proper heading hierarchies `<h1>` → `<h2>`).

### CSS & Design System
- Use **Vanilla CSS** with variables defined in `:root` (`--ink`, `--paper`, `--accent`, `--border`, `--font-display`, `--font-body`).
- Maintain visual consistency using `DM Serif Display` for headings and `DM Sans` for body text.
- Follow mobile-first/responsive design principles using `@media` breakpoints.
- Avoid inline styles in HTML unless required for dynamic layout calculations.

### JavaScript
- Use **Vanilla JavaScript** only — do not import third-party JS libraries.
- Wrap DOM manipulations inside `DOMContentLoaded` event listeners or scope functions cleanly.
- Perform presence checks (`if (!element) return;`) before accessing DOM elements.
- Clean up media/timers when closing overlays or modals (e.g., clearing `iframe.src` on modal close to halt audio/video playback).


<!-- Provide the road map of your project -->
---

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without flagging it — keep `pyproject.toml` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **`database/db.py` is currently empty** — do not assume helpers exist until the step that implements them
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- The app runs on **port 5001**, not the Flask default 5000 — don't change this
