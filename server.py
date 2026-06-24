"""
Laptop Remote — deployed server

Serves the landing page and the client executables for download.
No WebSocket relay — all logic runs inside the downloaded executable.
"""

import os

from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__)


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
        return send_from_directory(dist_dir, name, as_attachment=True)
    except FileNotFoundError:
        abort(404)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
