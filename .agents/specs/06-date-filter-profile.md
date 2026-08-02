# Spec: Date Filter for Profile Page

## Overview
This feature introduces date range filtering on the user profile dashboard (`/profile`). Users can filter their spending statistics, category breakdown, and recent transactions by specifying a custom start date and end date, or by using quick date presets (e.g., "This Month", "Last 30 Days", "All Time"). This enables users to analyze their financial behavior over specific time periods and track spending trends effectively.

## Depends on
- Step 01: Database Setup
- Step 02: Registration
- Step 03: Login and Logout
- Step 04: Profile Page

## Routes
- `GET /profile` — Display user profile dashboard filtered by optional `start_date` and `end_date` query parameters — logged-in users only.

## Database changes
No database changes.

## Templates
- **Create:** None
- **Modify:** `templates/profile.html` — Add a date range filter bar with start date, end date inputs, quick presets, and filter/clear buttons.

## Files to change
- `database/db.py` — Update database queries for stats, category breakdowns, and recent transactions to accept optional `start_date` and `end_date` parameters.
- `app.py` — Parse `start_date` and `end_date` query parameters in the `profile()` view function and pass them to database functions.
- `templates/profile.html` — Add the date filter form UI and bind date fields to current query parameters.
- `static/css/style.css` — Add styling for the date filter bar, form elements, buttons, and responsive layouts.

## Files to create
- `.agents/specs/06-date-filter-profile.md`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate date string format (YYYY-MM-DD) safely on backend
- Maintain date query parameters across page reloads / filter submits

## Definition of done
- User can select a `start_date` and `end_date` on `/profile` and submit the filter form.
- The metrics (Total Spent, Transactions, Top Category), category breakdown bar chart, and transactions list update according to the selected date range.
- Quick date filter options (e.g., "This Month", "Last 30 Days", "All Time") correctly populate date fields or apply filtering.
- Clicking "Clear Filter" resets the view to show all-time transactions.
- Invalid date formats or inverted date ranges (start > end) are handled gracefully without 500 errors.
