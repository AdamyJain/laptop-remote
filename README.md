# Laptop Remote

Turn your phone's browser into a touchpad + keyboard for your laptop, over
your local Wi-Fi. No app store, no native app — just a small Flask server on
the laptop and a web page you open on the phone.

```
[Phone browser]  --WebSocket-->  [Flask + Socket.IO server]  --pyautogui-->  [OS mouse/keyboard]
```

## 1. Install

Both the phone and laptop must be on the **same Wi-Fi network**.

```bash
cd laptop-remote
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_client.txt
```

### OS-specific notes (read the one that applies to you)

**macOS**
- Use **Python 3.12** (not 3.13/3.14 — some pinned deps lack wheels there):
  `python3.12 -m venv .venv`. Install it with `brew install python@3.12` if needed.
- Go to *System Settings → Privacy & Security → Accessibility*, then add your
  terminal app (Terminal/iTerm) or Python itself. Without this, pyautogui's
  clicks and key presses are silently ignored.
- The server listens on **port 5050** on macOS, because the built-in
  *AirPlay Receiver* (ControlCenter) permanently occupies port 5000. Override
  with `RC_PORT=...` if 5050 is also taken.
- **Running the prebuilt binary?** It's unsigned, so on first launch macOS
  blocks it: *"Apple could not verify 'LaptopRemote' is free of malware."*
  Click **Done** (not "Move to Trash"), then either go to *System Settings →
  Privacy & Security* and click **Open Anyway**, or clear the quarantine flag
  from a terminal:
  ```bash
  xattr -d com.apple.quarantine ~/Downloads/LaptopRemote
  ```
  First launch then takes ~20–30s while the single-file app unpacks — that's
  normal, not a hang. (Running from source with `python laptop_client.py`
  avoids both the Gatekeeper prompt and the slow startup.)
- Turn on **Mac modifiers** in the page's settings (gear icon) so Copy/Paste/
  Undo send ⌘ instead of Ctrl.

**Windows**
- Should work out of the box — no extra permissions needed.
- If Windows Defender Firewall prompts when you first run `server.py`,
  allow access on **Private networks**.

**Linux**
- Install Tk (pyautogui depends on it): `sudo apt install python3-tk python3-dev`
- pyautogui only works on **X11**, not native Wayland sessions. If you're on
  Wayland (most modern Ubuntu/Fedora desktops), either log into an "Ubuntu on
  Xorg" session at the login screen, or this won't be able to move the cursor.

## 2. Run

```bash
python laptop_client.py
```

This starts a local server, drops a tray icon in the menu bar, and opens a
**setup page** in your browser. The setup page shows a URL (and QR code) like:

```
http://192.168.1.42:5050/remote?token=<random-token>
```

A fresh token is generated each run. Open that exact URL in your phone's
browser (same Wi-Fi). The status dot in the top-left turns teal/green when
connected.

## 3. Using it

- **Touch surface** — drag with one finger to move the cursor, tap to left-click,
  two-finger tap to right-click.
- **Scroll rail** (right edge) — drag up/down to scroll.
- **Left / Double / Right** buttons — explicit clicks.
- **⌃ Keyboard** — opens your phone's keyboard; what you type is sent to the
  laptop as real keystrokes. Enter/Backspace are forwarded too.
- **Arrow keys, Esc, Tab, Space** — dedicated buttons.
- **Copy / Paste / Undo / Select All / App Switch** — sends the right
  modifier combo for your OS (toggle "Mac modifiers" in settings if needed).

## Security note

This only protects against casual access: anyone who can reach the server's
port on your LAN and guesses the token could control your laptop. It's meant
for trusted home/office Wi-Fi, not public networks. A fresh random token is
generated on every launch, so just restart the app to rotate it.

## Tuning

- **Pointer sensitivity** — slider in settings (gear icon), persisted in the
  page's local storage.
- **Port** — `RC_PORT=8080 python laptop_client.py` if 5050 is taken.

## Extending it

Everything funnels through a handful of Socket.IO events defined in
`server.py` (`move`, `click`, `doubleclick`, `scroll`, `key`, `hotkey`, `type`).
Adding a new button is: add a `<div class="keybtn">` in `templates/index.html`,
wire its click handler to `socket.emit(...)`, done.
