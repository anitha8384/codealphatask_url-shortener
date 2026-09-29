"""A small Flask URL shortener backed by SQLite."""

from __future__ import annotations

import os
import secrets
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "urls.db"
CODE_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CODE_LENGTH = 7

app = Flask(__name__)
app.config["DATABASE"] = str(DATABASE)


def get_db() -> sqlite3.Connection:
    """Get one SQLite connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with app.app_context():
        get_db().execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT NOT NULL UNIQUE,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        get_db().commit()


def validate_url(value: str) -> str | None:
    """Accept only absolute HTTP(S) URLs and return the cleaned input."""
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return url


def make_short_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def create_short_url(original_url: str) -> str:
    db = get_db()
    # A random 7-character base-62 code has trillions of possibilities; retry safely
    # in the exceptionally unlikely event of a database collision.
    while True:
        code = make_short_code()
        try:
            db.execute(
                "INSERT INTO urls (short_code, original_url) VALUES (?, ?)",
                (code, original_url),
            )
            db.commit()
            return code
        except sqlite3.IntegrityError:
            continue


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/shorten")
def shorten():
    """Create a short link. Send JSON {\"url\": \"https://...\"}."""
    payload = request.get_json(silent=True) or request.form
    original_url = validate_url(payload.get("url", ""))
    if original_url is None:
        return jsonify(error="Please provide a valid http:// or https:// URL."), 400

    code = create_short_url(original_url)
    short_url = url_for("follow_short_url", short_code=code, _external=True)
    return jsonify(short_code=code, original_url=original_url, short_url=short_url), 201


@app.get("/<short_code>")
def follow_short_url(short_code: str):
    row = get_db().execute(
        "SELECT original_url FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    if row is None:
        abort(404, description="This short URL does not exist.")
    return redirect(row["original_url"], code=302)


if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
