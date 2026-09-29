# Simple URL Shortener

A Flask + SQLite implementation of the internship task. It includes a JSON API, SQLite persistence, a redirect route, and a basic browser interface.

## Run it

```powershell
cd C:\Users\anith\Documents\Codex\2026-09-12\ho\outputs\url-shortener
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## API

Create a short URL:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:5000/api/shorten -ContentType 'application/json' -Body '{"url":"https://www.example.com/a-long-page"}'
```

Example response:

```json
{
  "original_url": "https://www.example.com/a-long-page",
  "short_code": "aB3kP9x",
  "short_url": "http://127.0.0.1:5000/aB3kP9x"
}
```

Visiting the returned `short_url` redirects to the saved original link. Data is stored in `urls.db`, automatically created on first run.
