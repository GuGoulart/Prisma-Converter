<div align="center">

# 🌐 PRISMA CONVERTER

### **Suite Universal de Procesamiento, Conversión y Seguridad de Archivos**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%Aas-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

<br/>

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/Framework-Flask-000000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7.svg?style=flat-square&logo=render&logoColor=white)](https://prisma-app.duckdns.org/)
[![Privacy First](https://img.shields.io/badge/Privacidad-100%25%20Segura-success.svg?style=flat-square&logo=shield&logoColor=white)](#-privacidad-y-seguridad)
[![License: GPL v3](https://img.shields.io/badge/Licencia-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

[🚀 Demostración en Vivo](https://prisma-app.duckdns.org/) • [✨ Funcionalidades](#-funcionalidades) • [⚡ Inicio Rápido](#-inicio-rápido-en-windows) • [🏗️ Arquitectura](#%EF%B8%8F-arquitectura-del-proyecto)


</div>

---

## 📖 Sobre el Proyecto

**Prisma Converter** es una plataforma web completa para la **conversión universal de archivos**, **manipulación avanzada de documentos PDF**, **encriptación AES-256** y **análisis de integridad de datos**.

Diseñado con un enfoque estricto en **Privacidad Primero (Privacy-First)** y alto rendimiento, el sistema procesa archivos con aislamiento de sesión mediante UUID v4 y eliminación automática de archivos temporales.

---

## ✨ Funcionalidades

### 🔄 Convertidor Universal de Archivos
* **Documentos y Hojas de Cálculo:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
* **Presentaciones:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
* **Estructuras de Datos:** `JSON ↔ CSV, XLSX, PDF`
* **Imágenes Modernas:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 🛠️ Herramientas Avanzadas de PDF y Archivos
| Categoría | Funcionalidades |
|---|---|
| 📄 **PDFs** | Unir, Dividir, Proteger/Desproteger con contraseña, Comprimir y Añadir Marca de Agua |
| 🖼️ **Imágenes** | Extracción masiva de medios desde PDF, Lector/Generador de QR Code y Extractor de Paleta de Colores |
| 🔒 **Seguridad** | Encriptación AES-256-CBC, Hashes Checksum (MD5, SHA1, SHA256) y ZIP protegido con contraseña |
| 📁 **Utilidades** | Renombrado automático en lote y Combinación de hojas de cálculo Excel/CSV |

---

## ⚡ Inicio Rápido en Windows

### Modos 1-Clic Automático (Modo Escritorio)
1. Clona este repositorio:
   ```bash
   git clone https://github.com/GuGoulart/Prisma-Converter.git
   cd Prisma-Converter
   ```
2. Haz **doble clic en el archivo `Prisma.bat`**.
   > El sistema creará automáticamente un acceso directo en tu Escritorio, iniciará el servidor local y abrirá tu navegador. ¡Al cerrar la pestaña del navegador, el servidor se apaga solo!

### Ejecución por Terminal / Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Abre en el navegador: `http://127.0.0.1:5000`

---

## 🏗️ Arquitectura del Proyecto

```text
Prisma-Converter/
├── app.py                      # Punto de entrada modular de la aplicación
├── routes/                     # Blueprints organizados por contexto
│   ├── views.py                # Rutas de páginas HTML y PWA
│   ├── converter.py            # Conversión universal de archivos
│   ├── pdf.py                  # Herramientas avanzadas de PDF
│   ├── file_tools.py           # Compresión, Encriptación y Hojas de cálculo
│   ├── tools.py                # Código QR y Paleta de Colores
│   └── history.py              # Historial de sesión y retención
├── core/                       # Reglas de negocio y motores
│   ├── utils.py                # Utilidades centralizadas
│   ├── security.py             # CSRF, Rate-limit y validación de Magic Bytes
│   ├── converter.py            # Motores de conversión
│   ├── pdf_tools.py            # Operaciones de PDF con PyMuPDF
│   └── tasks.py                # Procesamiento asíncrono de tareas
├── static/                     # CSS, JavaScript y recursos visuales
├── templates/                  # Plantillas HTML5 responsivas
└── scripts/                    # Scripts de inicio del sistema
```

---

## 🔒 Privacidad y Seguridad

* 🗑️ **Depuración Automática:** Los archivos temporales tienen políticas de retención configurables (Instantáneo, 5 min o 15 min) con eliminación permanente.
* 🛡️ **Defensa en Profundidad:** Protección contra Zip Bombs, verificación de firmas Magic Bytes y desinfección contra Path Traversal.

---

## 📜 Licencia

Distribuido bajo la licencia **GNU General Public License v3.0 (GPLv3)**.
Esta licencia garantiza que el código permanezca abierto y prohíbe expresamente la venta comercial no autorizada por terceros. Vea [LICENSE](LICENSE) para más detalles.

