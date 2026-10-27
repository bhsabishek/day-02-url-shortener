import secrets
import sqlite3
import string
from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import Flask, g, jsonify, redirect, request

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
MAX_CODE_ATTEMPTS = 5

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    code        TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    hits        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);
"""


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or "shortener.db"

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with sqlite3.connect(app.config["DB_PATH"]) as conn:
        conn.executescript(SCHEMA)

    def new_code():
        return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))

    def is_valid_url(url):
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/shorten")
    def shorten():
        body = request.get_json(silent=True) or {}
        url = body.get("url")
        if not isinstance(url, str) or not is_valid_url(url.strip()):
            return jsonify(error="a valid http(s) url is required"), 400
        url = url.strip()

        db = get_db()
        # Retry on the rare chance a random code is already taken.
        for _ in range(MAX_CODE_ATTEMPTS):
            code = new_code()
            try:
                db.execute(
                    "INSERT INTO links (code, url, created_at) VALUES (?, ?, ?)",
                    (code, url, datetime.now(timezone.utc).isoformat()),
                )
                db.commit()
                return jsonify(code=code, url=url), 201
            except sqlite3.IntegrityError:
                continue
        return jsonify(error="could not allocate a short code"), 500

    @app.get("/stats/<code>")
    def stats(code):
        row = get_db().execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
        if row is None:
            return jsonify(error="unknown code"), 404
        return jsonify(
            code=row["code"], url=row["url"], hits=row["hits"], created_at=row["created_at"]
        )

    @app.get("/<code>")
    def follow(code):
        db = get_db()
        row = db.execute("SELECT url FROM links WHERE code = ?", (code,)).fetchone()
        if row is None:
            return jsonify(error="unknown code"), 404
        db.execute("UPDATE links SET hits = hits + 1 WHERE code = ?", (code,))
        db.commit()
        return redirect(row["url"], code=302)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)