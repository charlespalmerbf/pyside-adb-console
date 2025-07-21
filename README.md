# PySide ADB Console

A retro-styled ADB Logcat viewer built with PySide6 and styled with the PressStart2P font for that classic 80s aesthetic.

## Features

- 📟 Retro pixel-style font (PressStart2P)
- 🎨 Light and Dark theme toggle
- 🧵 Real-time `adb logcat` stream viewer
- 🔍 Live filtering by keyword
- 🟥 Log level highlighting (e.g., ERROR in red, WARN in yellow)
- 🌈 Colored lines per log severity
- 🚫 Pause/resume live updates
- 🧹 Clear log buffer
- 📄 Export log output to a `.txt` file
- 📜 Auto-scroll toggle for better navigation

## Setup

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-repo/pyside-adb-console.git
    cd pyside-adb-console
    ```

2. **Create a virtual environment and activate it**:

    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    venv\Scripts\activate
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Ensure `adb` is available on your system path.** You can test this by running:

    ```bash
    adb devices
    ```

5. **Run the application**:

    ```bash
    python logcat_viewer.py
    ```

## File Structure

```
├── PressStart2P-Regular.ttf   # Retro font
├── logcat_viewer.py           # Main PySide6 application
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Notes

- The font `PressStart2P-Regular.ttf` should be in the project root.
- This viewer uses `adb logcat`, so a device must be connected and recognized by ADB.
- Tested with Python 3.10+ and PySide6.