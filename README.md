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
pip install -r requirements.txt
```

### OS-specific notes (read the one that applies to you)

**macOS**
- Go to *System Settings → Privacy & Security → Accessibility* and
  *Privacy & Security → Screen Recording*, then add your terminal app
  (Terminal/iTerm) or Python itself. Without this, pyautogui's clicks and
  key presses are silently ignored.
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
python server.py
```

It prints something like:

```
On your phone (same Wi-Fi), open:
  http://192.168.1.42:5000/?token=letmein
```

Open that exact URL in your phone's browser. The status dot in the top-left
turns teal/green when connected.

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
for trusted home/office Wi-Fi, not public networks. Change the default token:

```bash
RC_TOKEN=something-only-you-know python server.py
```

...and then open `http://<ip>:5000/?token=something-only-you-know` on your phone.

## Tuning

- **Pointer sensitivity** — slider in settings (gear icon), persisted in the
  page's local storage.
- **Port** — `RC_PORT=8080 python server.py` if 5000 is taken.

## Extending it

Everything funnels through a handful of Socket.IO events defined in
`server.py` (`move`, `click`, `doubleclick`, `scroll`, `key`, `hotkey`, `type`).
Adding a new button is: add a `<div class="keybtn">` in `templates/index.html`,
wire its click handler to `socket.emit(...)`, done.
