"""
Laptop Remote — deployed server

Serves the landing page and the client executables for download.
No WebSocket relay — all logic runs inside the downloaded executable.
"""

import base64
import json
import os
import threading
from datetime import datetime, timezone

from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Google Sheets download tracking
# ---------------------------------------------------------------------------

SPREADSHEET_ID = "1uQqicHDHIO9kVFGUhHNOqOpauXdTzh7Z-_9HjSvjMEc"
_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

try:
    import gspread
    from google.oauth2.service_account import Credentials as _SACredentials
    _SHEETS_OK = True
except ImportError:
    _SHEETS_OK = False


def _sheets_client():
    raw = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if not raw or not _SHEETS_OK:
        return None
    try:
        info = json.loads(base64.b64decode(raw))
        creds = _SACredentials.from_service_account_info(info, scopes=_SCOPES)
        return gspread.authorize(creds)
    except Exception:
        return None


def _ensure_summary(ws):
    if ws.cell(1, 1).value != "Platform":
        ws.update("A1:C4", [
            ["Platform", "Downloads", "Last Download"],
            ["Windows",  0,           "-"],
            ["Mac",      0,           "-"],
            ["Total",    "=B2+B3",    "-"],
        ])


def _record_download(platform: str):
    try:
        gc = _sheets_client()
        if not gc:
            return
        ss = gc.open_by_key(SPREADSHEET_ID)

        # --- summary sheet ---
        summary = ss.sheet1
        _ensure_summary(summary)
        row = 2 if platform == "windows" else 3
        current = int(summary.cell(row, 2).value or 0)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        summary.update(f"B{row}:C{row}", [[current + 1, now]])

        # --- log sheet (append) ---
        try:
            log = ss.worksheet("Log")
        except gspread.exceptions.WorksheetNotFound:
            log = ss.add_worksheet(title="Log", rows=5000, cols=2)
            log.append_row(["Timestamp", "Platform"])
        log.append_row([now, platform.capitalize()])
    except Exception:
        pass  # never let tracking break a download


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/download/<platform>")
def download(platform):
    filenames = {
        "windows": "LaptopRemote.exe",
        "mac":     "LaptopRemote",
    }
    name = filenames.get(platform)
    if not name:
        abort(404)
    dist_dir = os.path.join(app.root_path, "dist")
    try:
        response = send_from_directory(dist_dir, name, as_attachment=True)
        # Fire-and-forget: record the download without blocking the response
        threading.Thread(target=_record_download, args=(platform,), daemon=True).start()
        return response
    except FileNotFoundError:
        abort(404)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
