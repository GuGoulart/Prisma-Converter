<div align="center">

# 💎 PRISMA CONVERTER

### **Local Desktop Application • Complete File Conversion, Audio, Video, PDF & File Utilities Suite**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%Aas-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

<br/>

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-000000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20Desktop-0078D6.svg?style=flat-square&logo=windows&logoColor=white)](#-quick-start-on-windows)
[![100% Local & Private](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg?style=flat-square&logo=shield&logoColor=white)](#-privacy--security)
[![License: GPL v3](https://img.shields.io/badge/License-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

[✨ Features](#-features) • [⚡ Quick Start](#-quick-start-on-windows) • [🏗️ Architecture](#%EF%B8%8F-project-architecture) • [🔒 Privacy & Security](#-privacy--security)

</div>

---

## 📖 About the Project

**Prisma Converter** is a local desktop application and universal suite for **file conversion**, **advanced PDF document manipulation**, **audio & video editing/processing**, **media download by link**, and **data encryption**.

Unlike conventional online services, Prisma runs **100% locally on your machine**:
* 🛡️ **Absolute Privacy:** Your files never leave your computer and are never sent to external servers.
* ⚡ **Unlimited Upload:** Local processing with no file size limitations (`MAX_MB = 0`).
* 🪟 **Native App Window:** Runs in dedicated *App Mode* without browser address bar or tabs.

---

## ✨ Features

### 🔄 Universal Document Converter
* **Documents & Spreadsheets:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
* **Presentations:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
* **Data Structures:** `JSON ↔ CSV, XLSX, PDF`
* **Images:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 🎵 Audio Tools
* **Audio Conversion:** `MP3, WAV, FLAC, AAC, OGG, M4A` with bitrate and audio channels control.
* **Trim & Cut:** High-precision start and end markers to extract clips.
* **Enhancements:** Volume normalization and audio quality fine-tuning.
* **FFmpeg Auto-Setup:** Zero-config out of the box via `static-ffmpeg`.

### 🎬 Video Tools & Link Downloader
* **Video Conversion:** `MP4, MKV, AVI, MOV, WEBM` with resolution and codec options.
* **Video Compression:** Intelligent compression maintaining high visual fidelity.
* **Trim & Audio Extraction:** Extract soundtracks directly into MP3/WAV or clip segments.
* **Download by Link:** Download videos and audio from web URLs using `yt-dlp`.

### 🛠️ Advanced PDF & File Utilities
| Category | Features |
|---|---|
| 📄 **PDFs** | Merge, Split by pages, Password Protect/Unprotect, Compress, and Watermark |
| 🖼️ **Images** | PDF batch media extraction, QR Code generator/reader, and Color Palette extractor |
| 🔒 **Security** | AES-256-CBC Encryption, Checksum Hashes (MD5, SHA1, SHA256), and password-protected ZIPs |
| 📁 **Utilities** | Automated batch file renaming and Excel/CSV spreadsheet merging |

### 🎨 Modern Design & Customization
* **Custom Themes:** Dark and Light mode with **10 symmetrical pairs of accent colors**.
* **Unified Sidebar:** Direct navigation across all 6 sections (Home, Converter, Advanced Tools, Audio, Video, and History).
* **Internationalization (i18n):** Native support for English, Portuguese, and Spanish.

---

## ⚡ Quick Start on Windows

### 1-Click Desktop Shortcut (Recommended)

1. Clone or download the repository:
   ```bash
   git clone https://github.com/GuGoulart/Prisma-Converter.git
   cd Prisma-Converter
   ```

2. Install dependencies once:
   ```bash
   pip install -r requirements.txt
   ```

3. **Double-click `Prisma.bat`**:
   * Automatically creates the **"Prisma Converter"** shortcut on your Desktop with a custom icon.
   * Starts in the background and opens in a standalone desktop window.
   * If already open, clicking the shortcut simply focuses the window without port conflicts.

### Control Center (`Prisma.bat`)

The `Prisma.bat` file provides a convenient menu:
* `[1] Start Prisma Converter`: Launches the app silently in desktop mode.
* `[2] Stop Local Server`: Frees the port and shuts down background processes.
* `[3] Create/Update Shortcut`: Restores the Desktop shortcut.

### Direct Terminal Execution
```bash
python app.py
```
Opens directly in desktop app window mode (`http://127.0.0.1:5000`).

---

## 🏗️ Project Architecture

```text
Prisma-Converter/
├── app.py                      # Desktop app entry point
├── Prisma.bat                  # 1-click launcher & control center
├── requirements.txt            # Local Python dependencies
├── core/                       # Core business logic & processing engines
│   ├── converter.py            # Universal document/image converter
│   ├── pdf_tools.py            # PyMuPDF-based PDF manipulation
│   ├── audio_processor.py      # Audio conversion, trimming, and processing
│   ├── video_processor.py      # Video conversion & compression via FFmpeg
│   ├── video_downloader.py     # Link downloader powered by yt-dlp
│   ├── security.py             # CSRF validation, sanitization & encryption
│   ├── cleanup.py              # Automatic temp file garbage collection
│   └── utils.py                # System and file helper utilities
├── routes/                     # Context-specific Flask Blueprints
│   ├── views.py                # Main views (Home, Converter, Advanced)
│   ├── views_audio.py          # Audio and Video views
│   ├── converter.py            # Conversion API routes
│   ├── pdf.py                  # PDF API routes
│   ├── audio.py                # Audio API routes
│   ├── video.py                # Video & Downloader API routes
│   ├── file_tools.py           # Compression, Encryption & Sheets
│   ├── tools.py                # QR Code and Palette tools
│   └── history.py              # Local session history
├── static/                     # CSS, JavaScript, and graphical assets
│   ├── css/                    # Modular stylesheets (vars, layout, components)
│   ├── audio/                  # Dedicated audio/video styles and scripts
│   ├── theme_customizer.js     # Color theme customizer (10 pairs)
│   ├── i18n.js                 # Translations dictionary (EN / PT / ES)
│   └── logo.ico                # Desktop application icon
├── templates/                  # Responsive HTML templates & modals
└── scripts/                    # Windows desktop automation scripts
    ├── Iniciar_Prisma.vbs      # Silent background launcher (no CMD window)
    └── criar_atalho.ps1        # Desktop shortcut generator
```

---

## 🔒 Privacy & Security

* 💻 **100% Local Execution:** Everything stays on your computer; files are never transmitted across the public internet.
* 🗑️ **Automatic Cleanup:** Configurable temporary file lifecycle with immediate or scheduled deletion.
* 🛡️ **Defensive Engineering:** Strict filename sanitization against Path Traversal, Zip Bomb prevention, and MIME header validation.

---

## 📜 License

Distributed under the **GNU General Public License v3.0 (GPLv3)**.  
See [LICENSE](LICENSE) for more details.
