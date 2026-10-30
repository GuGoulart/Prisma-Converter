<div align="center">

# 💎 PRISMA CONVERTER

### **Local desktop app to convert, edit and protect files**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%AAs-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/Frontend-TypeScript-3178C6.svg?style=flat-square&logo=typescript&logoColor=white)](frontend/)
[![License: GPL v3](https://img.shields.io/badge/License-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

</div>

---

## About

Prisma runs on your computer and opens in its own window. Your files are processed locally and are not sent to any server. The only external connections are the ones you ask for: downloading a video from a link, and downloading the transcription model once.

## Features

| Area | Tools |
|---|---|
| **Converter** | PDF, DOCX, XLSX, CSV, JSON, PPT, PPTX, PNG, JPG, WEBP and HEIC, with preview |
| **PDF** | Merge, split, protect, unprotect, compress, watermark, extract images, remove and rotate pages |
| **Audio** | Convert, cut, join, adjust volume, normalize, change speed, reverse and transcribe |
| **Video** | Convert, compress, extract MP3, create GIF, remove audio, capture a frame and download from a link |
| **Files** | ZIP and TAR.GZ, password-protected ZIP, AES-256 encryption, hash, batch rename, merge spreadsheets |
| **Images** | Generate and read QR Codes, extract color palettes |

Every task shows its progress, can be canceled and goes through a queue, without freezing the rest of the app. Results stay in the history and are deleted according to the policy you choose: 5 minutes, 15 minutes or right after download.

### What needs external programs

The app detects what is installed and shows only the conversions that are possible.

| Feature | Requirement |
|---|---|
| Audio and video | [FFmpeg](https://ffmpeg.org/download.html). If it is not on the PATH, Prisma tries to download a copy automatically |
| DOCX, PPT and PPTX as source; spreadsheets to PDF or image | Microsoft Office **or** [LibreOffice](https://www.libreoffice.org/download/) |
| Text from images and scanned PDFs (OCR) | [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) |

## Quick start on Windows

Requirement: [Python 3.11 or newer](https://www.python.org/downloads/).

```bash
git clone https://github.com/GuGoulart/Prisma-Converter.git
```

Then double-click `Prisma.bat` and choose **[1] Start**. The first time, it installs the dependencies in a dedicated environment (`venv`) and creates a Desktop shortcut.

The server shuts down by itself a few minutes after the last window closes, as long as no task is running.

## Development

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
npm install

npm run watch         # rebuilds the frontend on save
python app.py

python -m pytest tests   # backend tests
npm run typecheck        # type checking
npm run e2e              # real browser tests
```

The frontend lives in `frontend/` and is compiled to `static/dist/`, which is versioned: **running the app does not require Node.js**. Run `npm run build` before committing frontend changes.

To update dependencies, edit `requirements.in` and regenerate `requirements.txt` in a clean environment.

## Privacy and security

- **Local processing:** the server listens only on `127.0.0.1` and pages load no external resources.
- **Protection against other sites:** `Host` and `Origin` validation, required CSRF token and a Content Security Policy without inline scripts.
- **Isolation:** downloads happen only by task ID. Submitted names and parameters never become disk paths.
- **Macros disabled** when opening documents through Office.
- **Deletion:** files are removed through the file system. This is not forensic destruction, which cannot be guaranteed on SSDs.

## License

Distributed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE).
