"""
Laptop Remote — self-contained client

Runs entirely on the user's laptop. Generates its own token, starts a local
Flask + SocketIO server, opens the setup page in the browser, and shows a
system tray icon for quitting cleanly.

Build:
    pip install -r requirements_client.txt
    pyinstaller --onefile --noconsole --name LaptopRemote \
                --add-data "templates;templates" laptop_client.py
"""

import os
import secrets
import socket
import subprocess
import sys
import threading
import webbrowser

import pyautogui
import pystray
from PIL import Image, ImageDraw
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TOKEN = secrets.token_urlsafe(12)
# Default 5050, not 5000: on macOS the ControlCenter "AirPlay Receiver"
# service permanently binds port 5000, which would make the server fail to start.
PORT  = int(os.environ.get("RC_PORT", 5050))

pyautogui.FAILSAFE = False
pyautogui.PAUSE    = 0

# ---------------------------------------------------------------------------
# Flask setup
# ---------------------------------------------------------------------------

if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(_base, "templates"))
app.config["SECRET_KEY"] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

phone_sid = None


def _lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    phone_url = f"http://{_lan_ip()}:{PORT}/remote?token={TOKEN}"
    return render_template("setup.html", phone_url=phone_url)


@app.route("/remote")
def remote():
    return render_template("remote.html")


@app.route("/help")
def help_page():
    return render_template("help.html")


# ---------------------------------------------------------------------------
# Socket — phone pairing
# ---------------------------------------------------------------------------

@socketio.on("phone_connect")
def on_phone_connect(data):
    global phone_sid
    if data.get("token") != TOKEN:
        emit("error", {"msg": "invalid token"})
        return
    phone_sid = request.sid
    emit("connected", {})
    emit("phone_joined", {}, broadcast=True, include_self=False)


@socketio.on("get_status")
def on_get_status():
    emit("status", {"phone_connected": phone_sid is not None})


@socketio.on("disconnect")
def on_disconnect():
    global phone_sid
    if request.sid == phone_sid:
        phone_sid = None
        emit("peer_disconnected", {}, broadcast=True)


# ---------------------------------------------------------------------------
# Socket — input relay → pyautogui
# ---------------------------------------------------------------------------

@socketio.on("move")
def handle_move(data):
    pyautogui.moveRel(float(data.get("dx", 0)), float(data.get("dy", 0)), duration=0)

@socketio.on("click")
def handle_click(data):
    pyautogui.click(button=data.get("button", "left"))

@socketio.on("doubleclick")
def handle_doubleclick(_):
    pyautogui.doubleClick()

@socketio.on("scroll")
def handle_scroll(data):
    amount = int(data.get("amount", 0))
    if amount:
        pyautogui.scroll(amount)

@socketio.on("key")
def handle_key(data):
    key = data.get("key")
    if key:
        pyautogui.press(key)

@socketio.on("hotkey")
def handle_hotkey(data):
    keys = data.get("keys", [])
    if keys:
        pyautogui.hotkey(*keys)

@socketio.on("type")
def handle_type(data):
    text = data.get("text", "")
    if text:
        pyautogui.typewrite(text, interval=0)

@socketio.on("brightness")
def handle_brightness(data):
    delta = int(data.get("delta", 10))
    if sys.platform == "win32":
        _adjust_brightness_win(delta)
    elif sys.platform == "darwin":
        # F1 / F2 = brightness down / up on most Mac keyboards
        pyautogui.press("f1" if delta < 0 else "f2")

def _adjust_brightness_win(delta):
    try:
        get_cmd = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
        r = subprocess.run(
            ["powershell", "-Command", get_cmd],
            capture_output=True, text=True, timeout=3,
        )
        current = int(r.stdout.strip())
        new_val = max(0, min(100, current + delta))
        set_cmd = (
            f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
            f".WmiSetBrightness(1, {new_val})"
        )
        subprocess.run(["powershell", "-Command", set_cmd], capture_output=True, timeout=3)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# System tray
# ---------------------------------------------------------------------------

def _make_tray_icon():
    """Draw a simple amber circle icon using Pillow."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill="#e8a33d")
    return img


def _build_tray(icon):
    icon.visible = True


def _quit(icon, _item):
    icon.stop()
    os._exit(0)


def _open_setup(icon, _item):
    webbrowser.open(f"http://localhost:{PORT}/")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(
        target=lambda: socketio.run(app, host="0.0.0.0", port=PORT, allow_unsafe_werkzeug=True),
        daemon=True,
    )
    server_thread.start()

    # Open browser after server has a moment to start
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}/")).start()

    # System tray icon runs on main thread (required on macOS; fine on Windows)
    tray = pystray.Icon(
        "LaptopRemote",
        _make_tray_icon(),
        "Laptop Remote",
        menu=pystray.Menu(
            pystray.MenuItem("Open setup page", _open_setup),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", _quit),
        ),
    )
    tray.run(_build_tray)
