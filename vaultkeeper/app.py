"""
VaultKeeper - A simple encrypted password manager
Built with Flask, SQLite, and Fernet encryption

Author: Yash (BCA Project)
"""

import os
import sqlite3
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key-before-deploying")

# On Render's free tier the filesystem resets on redeploy/restart, so vault
# data won't persist forever across deploys unless you attach a paid disk.
# For a class project this is fine — data survives while the app is running.
DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "vault.db")
KEY_PATH = os.path.join(os.path.dirname(__file__), "instance", "secret.key")


# ---------------------------------------------------------------------------
# Encryption key setup
# ---------------------------------------------------------------------------
def load_or_create_key():
    """Load the Fernet key from disk, or create one if it doesn't exist yet."""
    os.makedirs(os.path.dirname(KEY_PATH), exist_ok=True)
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)
    return key


FERNET = Fernet(load_or_create_key())


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vault_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            site_name TEXT NOT NULL,
            site_username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Routes: Auth
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("register"))

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing:
            flash("Username already taken.", "danger")
            conn.close()
            return redirect(url_for("register"))

        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
        conn.close()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes: Vault
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    items = conn.execute(
        "SELECT * FROM vault_items WHERE user_id = ? ORDER BY site_name",
        (session["user_id"],),
    ).fetchall()
    conn.close()

    decrypted_items = []
    for item in items:
        decrypted_items.append(
            {
                "id": item["id"],
                "site_name": item["site_name"],
                "site_username": item["site_username"],
                "password": FERNET.decrypt(item["encrypted_password"].encode()).decode(),
                "notes": item["notes"],
            }
        )

    return render_template("dashboard.html", items=decrypted_items, username=session["username"])


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        site_name = request.form.get("site_name", "").strip()
        site_username = request.form.get("site_username", "").strip()
        password = request.form.get("password", "")
        notes = request.form.get("notes", "").strip()

        if not site_name or not site_username or not password:
            flash("Site name, username, and password are required.", "danger")
            return redirect(url_for("add_item"))

        encrypted = FERNET.encrypt(password.encode()).decode()

        conn = get_db()
        conn.execute(
            """INSERT INTO vault_items (user_id, site_name, site_username, encrypted_password, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (session["user_id"], site_name, site_username, encrypted, notes),
        )
        conn.commit()
        conn.close()

        flash("Password saved to vault.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_item.html")


@app.route("/delete/<int:item_id>")
@login_required
def delete_item(item_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM vault_items WHERE id = ? AND user_id = ?",
        (item_id, session["user_id"]),
    )
    conn.commit()
    conn.close()
    flash("Entry deleted.", "info")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# Make sure the database exists whether run via `python app.py`
# (local dev) or via gunicorn (production/Render)
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# Entry point (local development only)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)