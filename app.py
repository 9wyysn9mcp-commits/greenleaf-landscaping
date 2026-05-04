from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"

BUSINESS_NAME   = "GreenLeaf Landscaping"
ADMIN_PASSWORD  = "greenleaf2024"

NOTIFY_EMAIL    = "Nicolas.lemieux28@icloud.com"
SMTP_USER       = "Nicolas.lemieux28@icloud.com"
SMTP_PASSWORD   = os.environ.get("SMTP_PASSWORD", "yiat-vmdc-xtas-smsi")
SMTP_HOST       = "smtp.mail.me.com"
SMTP_PORT       = 587

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "quotes.db"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                services TEXT,
                message TEXT,
                preferred_date TEXT,
                submitted_at TEXT NOT NULL,
                status TEXT DEFAULT 'new'
            )
        """)
        conn.commit()


def _send_email(name, email, phone, address, services, message, preferred_date):
    subject = f"New Quote Request — {name}"
    body = f"""
New quote request from your website!

Name:           {name}
Email:          {email}
Phone:          {phone or '—'}
Address:        {address or '—'}
Services:       {services or '—'}
Preferred Date: {preferred_date or '—'}

Message:
{message or '—'}

---
Reply directly to {email} or call/text {phone}.
    """.strip()

    msg = MIMEMultipart()
    msg["From"]     = SMTP_USER
    msg["To"]       = NOTIFY_EMAIL
    msg["Subject"]  = subject
    msg["Reply-To"] = email
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, NOTIFY_EMAIL, msg.as_string())
        print("[email] Notification sent.")
    except Exception as e:
        print(f"[email] Failed: {e}")


def send_notification_async(name, email, phone, address, services, message, preferred_date):
    # Run in background thread so it never blocks or times out the request
    t = threading.Thread(
        target=_send_email,
        args=(name, email, phone, address, services, message, preferred_date),
        daemon=True,
    )
    t.start()


try:
    init_db()
except Exception as e:
    print(f"[db] Init failed: {e}")


@app.route("/")
def index():
    return render_template("index.html", business_name=BUSINESS_NAME)


@app.route("/quote", methods=["POST"])
def submit_quote():
    try:
        data = request.get_json(force=True, silent=True) or {}

        name           = str(data.get("name", "")).strip()
        email          = str(data.get("email", "")).strip()
        phone          = str(data.get("phone", "")).strip()
        address        = str(data.get("address", "")).strip()
        services       = ", ".join(data.get("services", []))
        message        = str(data.get("message", "")).strip()
        preferred_date = str(data.get("preferred_date", "")).strip()

        if not name or not email:
            return jsonify({"success": False, "error": "Name and email are required."}), 400

        # Fire email in background — never blocks the response
        send_notification_async(name, email, phone, address, services, message, preferred_date)

        # Save to DB
        try:
            with get_db() as conn:
                conn.execute(
                    """INSERT INTO quotes
                       (name, email, phone, address, services, message, preferred_date, submitted_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name, email, phone, address, services, message, preferred_date,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )
                conn.commit()
        except Exception as e:
            print(f"[db] Save failed: {e}")

        return jsonify({"success": True, "message": "Quote request received! We'll be in touch soon."})

    except Exception as e:
        print(f"[quote] Unexpected error: {e}")
        return jsonify({"success": False, "error": "Something went wrong. Please text us at (647) 215-4544."}), 500


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
        else:
            return render_template("admin.html", error="Incorrect password", logged_in=False,
                                   business_name=BUSINESS_NAME)

    if not session.get("admin"):
        return render_template("admin.html", logged_in=False, business_name=BUSINESS_NAME)

    try:
        with get_db() as conn:
            quotes = conn.execute("SELECT * FROM quotes ORDER BY submitted_at DESC").fetchall()
    except Exception:
        quotes = []

    return render_template("admin.html", logged_in=True, quotes=quotes, business_name=BUSINESS_NAME)


@app.route("/admin/update-status", methods=["POST"])
def update_status():
    if not session.get("admin"):
        return jsonify({"success": False}), 403
    data = request.get_json()
    with get_db() as conn:
        conn.execute("UPDATE quotes SET status=? WHERE id=?", (data["status"], data["id"]))
        conn.commit()
    return jsonify({"success": True})


@app.route("/admin/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5050))
    app.run(debug=False, host="0.0.0.0", port=port)
