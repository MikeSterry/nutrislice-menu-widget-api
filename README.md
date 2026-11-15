# Echo Park Elementary Menu API

Flask API + embeddable widgets for Echo Park Elementary (District 196 / Nutrislice).

## Endpoints

### JSON
`/api?view=week|remainder|today|tomorrow[&date=YYYY-MM-DD]`

- `week` = Mon–Fri for the week containing `date` (defaults to today)
- `remainder` = from `date` through Fri of that week (inclusive)
- `today` = menu for `date`
- `tomorrow` = menu for `date+1`

### Widgets (HTML)
`/widget?view=week|today|tomorrow[&date=YYYY-MM-DD][&theme=light|dark|transparent]`

- `week` highlights the requested `date` as “today”
- theme controls CSS variables via `body[data-theme]`

### Calendar subscriptions (iCalendar)

| Endpoint | Events |
| --- | --- |
| `/calendar/all.ics` | All four menu categories and published school closures |
| `/calendar/breakfast.ics` | Breakfast |
| `/calendar/lunch.ics` | Lunch |
| `/calendar/grab-and-go.ics` | Grab & Go |
| `/calendar/deli-entree.ics` | Deli Entree |

Each feed includes published menu entries as all-day events for the current
school week and the next three weeks, using the app's configured time zone.
Subscribe to a full feed URL in your calendar app to receive menu updates.

### Health
`/health`

## Config (env overrides)

See `.env.example`.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.main:app
flask run --port 8080
```

## Run with Docker
```bash
docker compose up --build
```


### Run via shim
```bash
python run.py
```
