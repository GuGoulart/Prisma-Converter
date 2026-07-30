# PRISMA CONVERTER — Suite Universal de Procesamiento de Archivos

<div align="center">

![Prisma Logo Header](../static/favicon.svg)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/framework-Flask-000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg?style=for-the-badge)](../README.md#licen%C3%A7a)
[![PWA Ready](https://img.shields.io/badge/PWA-Enabled-success.svg?style=for-the-badge&logo=pwa&logoColor=white)](../static/manifest.json)
[![Deploy Status](https://img.shields.io/badge/deploy-Render%20%7C%20Cloud%20Run-brightgreen.svg?style=for-the-badge&logo=googlecloud&logoColor=white)](https://prisma-vmbr.onrender.com/)

**[ 🇧🇷 Português ](../README.md) | [ 🇺🇸 English ](README.en.md) | [ 🇪🇸 Español ](README.es.md)**

*Tú lo piensas. Prisma lo hace. De conversiones universales a manipulación avanzada de archivos, todo en un solo lugar.*

[Demostración en Vivo](https://prisma-vmbr.onrender.com/) • [Guía de Instalación Desktop](installation/desktop.es.md) • [Guía de Instalación Mobile PWA](installation/mobile.es.md)

</div>

---

## 📋 Índice

- [Visión General](#-visión-general)
- [Funcionalidades Principales](#-funcionalidades-principales)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Requisitos Mínimos](#-requisitos-mínimos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Ejecución](#-ejecución)
- [Estructura de Directorios](#-estructura-de-directorios)
- [Seguridad y Privacidad](#-seguridad-y-privacidad)
- [Licencia](#-licencia)

---

## 🌟 Visión General

**Prisma Converter** es una **Aplicación Web (SaaS) / Progressive Web App (PWA)** de nivel comercial diseñada para conversión universal de archivos, manipulación avanzada de documentos PDF, herramientas de medios y ciberseguridad directamente en el navegador.

Con un enfoque centrado en la **privacidad como prioridad (Privacy-First)**, procesamiento de alta velocidad y experiencia intuitiva, el sistema realiza transformaciones complejas (como PDF a XLSX con extracción tabular inteligente, conversiones cruzadas de formato, encriptación AES-256 y extracción de paletas de colores) mediante procesamiento temporal aislado con **incineración automática inmediata** de archivos tras su uso.

---

## 🚀 Funcionalidades Principales

### 1. 🔄 Conversor Universal Inteligente (52 Rutas Cruzadas)
A través de un Hub de Conversión dinámico (`_via_pdf`), los archivos transicionan entre formatos no compatibles de forma nativa:
- **Documentos y Hojas de Cálculo:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
- **Presentaciones:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
- **Datos y Web:** `JSON ↔ CSV, XLSX, PDF`
- **Imágenes Modernas:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 2. 📄 Herramientas Avanzadas de PDF e Imágenes
- **Unir PDFs:** Combinación ordenada de múltiples documentos PDF en un solo archivo.
- **Dividir PDF:** División por rangos, páginas individuales o bloques fijos comprimidos en `.zip`.
- **Proteger / Desproteger PDF:** Encriptación y desencriptación con contraseña vía PyMuPDF (`fitz`).
- **Marca de Agua:** Superposición de texto personalizado en PDFs.
- **Extracción de Medios:** Extrae imágenes integradas de alta resolución.
- **Lector y Generador de QR Code:** Procesamiento inteligente vía AJAX.
- **Extractor de Paleta de Colores:** Análisis K-Means de colores dominantes con códigos HEX.

---

## 💻 Requisitos e Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/GuGoulart/prisma-converter.git
cd prisma-converter

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar servidor
python app.py
```

Acceda a la aplicación en su navegador en `http://127.0.0.1:5000`.

Para guías detalladas por plataforma, consulte la [Guía de Instalación Desktop](installation/desktop.es.md) y la [Guía de Instalación Mobile PWA](installation/mobile.es.md).

---

## 📄 Licencia

**Todos los derechos reservados.**  
Copyright (c) Gustavo Goulart Bretas. Para consultas corporativas o autorizaciones, visite [github.com/GuGoulart](https://github.com/GuGoulart).
