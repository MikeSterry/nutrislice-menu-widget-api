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
