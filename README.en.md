<div align="center">

# 🌐 PRISMA CONVERTER

### **Universal File Processing, Conversion & Security Suite**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%Aas-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

<br/>

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/Framework-Flask-000000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7.svg?style=flat-square&logo=render&logoColor=white)](https://prisma-app.duckdns.org/)
[![Privacy First](https://img.shields.io/badge/Privacy-100%25%20Secure-success.svg?style=flat-square&logo=shield&logoColor=white)](#-privacy--security)
[![License: GPL v3](https://img.shields.io/badge/License-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

[🚀 Live Demo](https://prisma-app.duckdns.org/) • [✨ Features](#-features) • [⚡ Quick Start](#-quick-start-on-windows) • [🏗️ Architecture](#%EF%B8%8F-project-architecture)


</div>

---

## 📖 About the Project

**Prisma Converter** is a comprehensive web platform for **universal file conversion**, **advanced PDF document manipulation**, **AES-256 encryption**, and **data integrity analysis**.

Engineered with a strict **Privacy-First** approach and high performance, the system processes conversions with UUID v4 session isolation and automatic temporary file purging.

---

## ✨ Features

### 🔄 Universal File Converter
* **Documents & Spreadsheets:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
* **Presentations:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
* **Data Structures:** `JSON ↔ CSV, XLSX, PDF`
* **Modern Images:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 🛠️ Advanced PDF & File Tools
| Category | Features |
|---|---|
| 📄 **PDFs** | Merge, Split, Password Protect/Unprotect, Compress, and Watermark |
| 🖼️ **Images** | PDF batch media extractor, QR Code generator/reader, and Color Palette extractor |
| 🔒 **Security** | AES-256-CBC Encryption, Checksum Hashes (MD5, SHA1, SHA256), and Password-protected ZIPs |
| 📁 **Utilities** | Automated batch file renaming and Excel/CSV spreadsheet merging |

---

## ⚡ Quick Start on Windows

### Automatic 1-Click (Desktop Mode)
1. Clone this repository:
   ```bash
   git clone https://github.com/GuGoulart/Prisma-Converter.git
   cd Prisma-Converter
   ```
2. Double-click the **`Prisma.bat`** file.
   > The app automatically creates a Desktop shortcut, starts the local server, and launches your web browser. Closing the browser tab automatically stops the server!

### Terminal / Linux / macOS Execution
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open in browser: `http://127.0.0.1:5000`

---

## 🏗️ Project Architecture

```text
Prisma-Converter/
├── app.py                      # Modular application entrypoint
├── routes/                     # Contextual Flask Blueprints
│   ├── views.py                # HTML page routes and PWA assets
│   ├── converter.py            # Universal file conversion
│   ├── pdf.py                  # Advanced PDF tools
│   ├── file_tools.py           # Compression, Encryption & Spreadsheets
│   ├── tools.py                # QR Code & Color Palette
│   └── history.py              # Session history and retention
├── core/                       # Core engine and business rules
│   ├── utils.py                # Centralized route utilities
│   ├── security.py             # CSRF, Rate-limiting & Magic Bytes validation
│   ├── converter.py            # Conversion engines
│   ├── pdf_tools.py            # PyMuPDF document operations
│   └── tasks.py                # Async background tasks
├── static/                     # CSS, JavaScript & visual assets
├── templates/                  # Responsive HTML5 templates
└── scripts/                    # Windows system launcher scripts
```

---

## 🔒 Privacy & Security

* 🗑️ **Automatic Purging:** Temporary files have configurable retention policies (Instant, 5 min, or 15 min) with permanent deletion.
* 🛡️ **Defense-in-Depth:** Zip Bomb protection, Magic Bytes signature verification, and Path Traversal sanitization.

---

## 📜 License

Distributed under the **GNU General Public License v3.0 (GPLv3)**.
This license guarantees the code remains open-source and strictly prohibits unauthorized commercial reselling by third parties. See [LICENSE](LICENSE) for details.

