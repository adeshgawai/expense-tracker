# Spec: Profile Page Design

## Overview
Implements the user profile page (`GET /profile`) and profile summary dashboard for Spendly. Once a user is authenticated, navigating to `/profile` displays their account details (name, email address, registration date), financial summary metrics (total expenses count and total amount spent), and account management actions. Unauthenticated users attempting to view `/profile` are redirected to the login page with an informative flash message. The page features a premium, responsive vanilla CSS design adhering strictly to Spendly's design system (`DM Serif Display` headings, `DM Sans` body, card components, and CSS variables).

## Depends on
- Step 01: Database Setup (`01-database-setup.md`)
- Step 02: Registration (`02-registration.md`)
- Step 03: Login and Logout (`03-login-logout.md`)

## Routes
- `GET /profile` — Renders profile dashboard with user account details and activity summary — Logged-in (redirects unauthenticated users to `/login`)

## Database changes
No database changes.

## Templates
- **Create:**
  - `templates/profile.html`: User profile view extending `base.html` displaying user avatar/header, account details, financial stats, and quick actions.
- **Modify:**
  - `templates/base.html`: Ensure header navbar includes direct link to Profile page when user is logged in.

## Files to change
- `app.py` — Replace stub `profile()` handler with logic verifying `session.get('user_id')`, fetching user details and expense summary stats from database, and rendering `profile.html`.
- `database/db.py` — Add `get_user_by_id(user_id)` and `get_user_profile_stats(user_id)` database helper functions.
- `static/css/style.css` — Add custom styling for profile layout, avatar header, info cards, stat badges, and action buttons using CSS custom variables.
- `templates/base.html` — Update navigation bar links for authenticated users to include Profile page link.

## Files to create
- `templates/profile.html` — User profile template extending `base.html`.
- `tests/test_profile.py` — Pytest suite testing profile authentication protection, data rendering, and layout integrity.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Always use `url_for()` for template links and route redirects
- Redirect unauthenticated users to `url_for('login')`

## Definition of done
- [ ] `GET /profile` redirects unauthenticated users to `/login` with an informative warning/flash message
- [ ] `GET /profile` for logged-in user renders `templates/profile.html` successfully
- [ ] Profile page displays user name, email, and formatted member registration date (`created_at`)
- [ ] Profile page displays summary expenditure metrics (total expense count and total amount spent)
- [ ] Base template navigation bar includes a link to the Profile page when logged in
- [ ] Profile interface adheres to Spendly design system (CSS variables, DM fonts, clean responsive layout)
- [ ] All tests in `tests/test_profile.py` pass via `pytest`
