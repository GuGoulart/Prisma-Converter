# PRISMA CONVERTER — Universal File Processing Suite

<div align="center">

![Prisma Logo Header](../static/favicon.svg)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/framework-Flask-000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg?style=for-the-badge)](../README.md#licen%C3%A7a)
[![PWA Ready](https://img.shields.io/badge/PWA-Enabled-success.svg?style=for-the-badge&logo=pwa&logoColor=white)](../static/manifest.json)
[![Deploy Status](https://img.shields.io/badge/deploy-Render%20%7C%20Cloud%20Run-brightgreen.svg?style=for-the-badge&logo=googlecloud&logoColor=white)](https://prisma-vmbr.onrender.com/)

**[ 🇧🇷 Português ](../README.md) | [ 🇺🇸 English ](README.en.md) | [ 🇪🇸 Español ](README.es.md)**

*You think it. Prisma does it. From universal conversions to advanced file manipulation, all in one place.*

[Live Demo](https://prisma-vmbr.onrender.com/) • [Desktop Installation Guide](installation/desktop.en.md) • [Mobile PWA Installation Guide](installation/mobile.en.md)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Application Data Flow](#-application-data-flow)
- [Minimum Requirements & Prerequisites](#-minimum-requirements--prerequisites)
- [Complete Installation & Setup](#-complete-installation--setup)
- [Execution](#-execution)
- [Directory Structure](#-directory-structure)
- [Detailed Module Guide](#-detailed-module-guide)
- [Layered Security & Privacy](#-layered-security--privacy)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Usage Tips & Best Practices](#-usage-tips--best-practices)
- [License](#-license)

---

## 🌟 Overview

**Prisma Converter** is a commercial-grade **Web Application (SaaS) / Progressive Web App (PWA)** designed for universal file conversion, advanced PDF document manipulation, media processing utilities, and cybersecurity tools directly inside the browser.

Built with a **Privacy-First** design philosophy, ultra-fast execution, and seamless UX, the system performs complex file transformations (such as PDF to XLSX with tabular AI extraction, multi-format cross conversions, AES-256 encryption, and image palette extraction) using isolated temporary processing and **immediate automatic file incineration** right after use.

---

## 🚀 Key Features

### 1. 🔄 Smart Universal Converter (52 Cross Routes)
Utilizing a dynamic Conversion Hub (`_via_pdf`), files transition seamlessly between natively incompatible formats:
- **Documents & Spreadsheets:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
- **Presentations:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
- **Data & Web:** `JSON ↔ CSV, XLSX, PDF`
- **Modern Images:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 2. 📄 Advanced PDF & Image Tools
- **Merge PDFs:** Ordered combination of multiple PDF documents into a single unified file.
- **Split PDF:** Division by custom page range, single pages, or fixed chunks with compressed `.zip` output.
- **Protect / Unprotect PDF:** Password encryption and decryption via PyMuPDF (`fitz`).
- **Watermark:** Custom text watermark overlay on PDFs.
- **Media Extraction:** Extract high-resolution embedded images from PDF pages.
- **QR Code Reader & Generator:** AJAX-based generation and reading.
- **Color Palette Extractor:** K-Means clustering analysis of dominant colors with HEX codes and visual swatches.

### 3. 🛡️ Security & File Modification
- **AES-256 Encryption:** File encryption and decryption.
- **ZIP / TAR.GZ Compression:** Compressed archives with password protection.
- **Hash Integrity Verification:** Instant calculation of `MD5`, `SHA-1`, and `SHA-256` checksums with 1-click copy.
- **Batch Renamer:** Automated file batch renaming.

---

## 🛠️ Tech Stack

| Layer | Technology | Primary Function |
|---|---|---|
| **Backend** | Python 3.10+ | Core server logic & conversion engines |
| **Web Framework** | Flask 3.0+ | HTTP routing, session management, security headers |
| **PDF Engine** | PyMuPDF (`fitz`) / pdf2docx | Rendering, extraction, merging, and encryption |
| **Tabular Extractor**| pdfplumber | PDF table extraction to XLSX/CSV |
| **Data Processing**| pandas + openpyxl | CSV, XLSX, and JSON structure processing |
| **Image Processing**| Pillow (PIL) | Manipulation, conversion, and color extraction |
| **Office Engine** | pywin32 / LibreOffice CLI | High-fidelity rendering for MS Office formats |
| **Security & Cryptography**| cryptography / hashlib | AES-256 encryption and Hash calculation |
| **Frontend** | HTML5 / Vanilla CSS / JS | Lightweight responsive UI, dark/light theme |
| **PWA & Mobile** | Service Worker + Manifest v3 | Offline PWA caching, mobile shortcuts |
| **Deployment** | Gunicorn / Docker | WSGI server for cloud production environments |

---

## 🏗️ System Architecture

```
                  ┌────────────────────────────────────────┐
                  │          Web / Mobile Client           │
                  │   (HTML5 / Vanilla JS / PWA / Service) │
                  └───────────────────┬────────────────────┘
                                      │  HTTP POST / GET
                                      ▼
                  ┌────────────────────────────────────────┐
                  │              Flask Server              │
                  │ (Routes, CSRF Validation, Rate Limit)  │
                  └───────────────────┬────────────────────┘
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
┌───────────────────┐                                   ┌───────────────────┐
│     core/         │                                   │     core/         │
│  converter.py     │                                   │   pdf_tools.py    │
│ (Hub _via_pdf,    │                                   │ (PyMuPDF, FitZ,   │
│  LibreOffice/Win) │                                   │  Merge, Split)    │
└─────────┬─────────┘                                   └─────────┬─────────┘
          │                                                       │
          └───────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │         Cleanup & Incineration         │
                  │ (@after_this_request + core/cleanup.py)│
                  └────────────────────────────────────────┘
```

---

## 💻 Minimum Requirements & Prerequisites

### System Requirements
- **OS:** Windows 10/11, macOS 11+ (Intel / Apple Silicon), or Linux (Ubuntu 20.04+, Debian 11+).
- **CPU:** Dual-core 2.0 GHz or higher.
- **RAM:** 2 GB minimum (4 GB recommended for concurrent file processing).
- **Disk Space:** 500 MB free space.

---

## 📦 Complete Installation & Setup

```bash
# 1. Clone repository
git clone https://github.com/GuGoulart/prisma-converter.git
cd prisma-converter

# 2. Virtual environment setup
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Environment configuration (.env)
cp .env.example .env

# 5. Run local server
python app.py
```

Access the application in your browser at `http://127.0.0.1:5000`.

For detailed OS-specific setup, consult the [Desktop Installation Guide](installation/desktop.en.md) and [Mobile PWA Installation Guide](installation/mobile.en.md).

---

## 📄 License

**All rights reserved.**  
Copyright (c) Gustavo Goulart Bretas. For permissions or corporate inquiries, visit [github.com/GuGoulart](https://github.com/GuGoulart).
