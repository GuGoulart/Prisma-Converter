<div align="center">

# 💎 PRISMA CONVERTER

### **Aplicación de Escritorio Local • Suite Completa de Conversión, Audio, Video, PDF y Utilidades**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%Aas-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

<br/>

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-000000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows%20Desktop-0078D6.svg?style=flat-square&logo=windows&logoColor=white)](#-inicio-rápido-en-windows)
[![100% Local y Privado](https://img.shields.io/badge/Privacidad-100%25%20Local-success.svg?style=flat-square&logo=shield&logoColor=white)](#-privacidad-y-seguridad)
[![Licencia: GPL v3](https://img.shields.io/badge/Licencia-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

[✨ Funcionalidades](#-funcionalidades) • [⚡ Inicio Rápido](#-inicio-rápido-en-windows) • [🏗️ Arquitectura](#%EF%B8%8F-arquitectura-del-proyecto) • [🔒 Privacidad y Seguridad](#-privacidad-y-seguridad)

</div>

---

## 📖 Acerca del Proyecto

**Prisma Converter** es una aplicación de escritorio local y suite universal para la **conversión de archivos**, **manipulación avanzada de PDFs**, **edición y procesamiento de audio y video**, **descarga de medios por enlace** y **cifrado de datos**.

A diferencia de los servicios en línea tradicionales, Prisma funciona **100% de manera local en tu ordenador**:
* 🛡️ **Privacidad Absoluta:** Tus archivos nunca salen de tu equipo y no se envían a servidores externos.
* ⚡ **Sin Límites de Tamaño:** Procesamiento local sin restricciones de carga (`MAX_MB = 0`).
* 🪟 **Ventana de Aplicación Nativa:** Se ejecuta en modo ventana independiente (*App Mode*), sin barras de navegación ni pestañas del navegador.

---

## ✨ Funcionalidades

### 🔄 Conversor Universal de Documentos
* **Documentos y Hojas de Cálculo:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
* **Presentaciones:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
* **Estructuras de Datos:** `JSON ↔ CSV, XLSX, PDF`
* **Imágenes:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 🎵 Herramientas de Audio
* **Conversión de Audio:** `MP3, WAV, FLAC, AAC, OGG, M4A` con ajuste de tasa de bits y canales.
* **Corte y Recorte:** Marcadores de inicio y fin con alta precisión para extraer fragmentos.
* **Ajustes:** Normalización de volumen y control de fidelidad de audio.
* **Configuración automática de FFmpeg:** Listo para usar sin configurar variables de entorno (`static-ffmpeg`).

### 🎬 Herramientas de Video y Descarga
* **Conversión de Video:** `MP4, MKV, AVI, MOV, WEBM` con control de resolución y códecs.
* **Compresión Inteligente:** Reduce el peso manteniendo una excelente calidad visual.
* **Corte y Extracción:** Recorte de escenas y extracción directa de pista de audio a MP3/WAV.
* **Descarga por Enlace:** Descarga de videos y audios desde URLs de internet mediante `yt-dlp`.

### 🛠️ Herramientas Avanzadas de PDF y Utilidades
| Categoría | Funcionalidades |
|---|---|
| 📄 **PDFs** | Unir múltiples PDFs, Dividir por páginas, Proteger/Desproteger con contraseña, Comprimir y Añadir Marca de Agua |
| 🖼️ **Imágenes** | Extracción masiva de imágenes de PDF, Generador/Lector de Códigos QR y Extractor de Paleta de Colores |
| 🔒 **Seguridad** | Cifrado AES-256-CBC, Verificación por Hashes (MD5, SHA1, SHA256) y creación de ZIP protegido con contraseña |
| 📁 **Utilidades** | Renombrado masivo inteligente y Fusión de hojas de cálculo Excel/CSV |

### 🎨 Diseño Moderno y Personalización
* **Temas Personalizables:** Modo Oscuro y Modo Claro con **10 colores simétricos** en pares.
* **Barra Lateral Unificada:** Acceso directo a las 6 secciones (Inicio, Conversor, Herramientas Avanzadas, Audio, Video e Historial).
* **Internacionalización (i18n):** Soporte nativo para Español, Portugués e Inglés.

---

## ⚡ Inicio Rápido en Windows

### Acceso Directo en el Escritorio en 1-Clic (Recomendado)

1. Clona o descarga el repositorio:
   ```bash
   git clone https://github.com/GuGoulart/Prisma-Converter.git
   cd Prisma-Converter
   ```

2. Instala las dependencias necesarias una única vez:
   ```bash
   pip install -r requirements.txt
   ```

3. Haz **doble clic en `Prisma.bat`**:
   * Creará automáticamente el acceso directo **"Prisma Converter"** en tu Escritorio con el icono personalizado.
   * La aplicación arrancará en segundo plano y se abrirá en una ventana nativa de escritorio.
   * Si ya está abierta y pulsas de nuevo el acceso directo, simplemente enfocará la ventana activa.

### Panel de Control (`Prisma.bat`)

El archivo `Prisma.bat` incluye un menú interactivo:
* `[1] Iniciar Prisma Converter`: Ejecución silenciosa en modo ventana.
* `[2] Detener Servidor Local`: Cierra procesos y libera el puerto.
* `[3] Crear/Actualizar Acceso Directo`: Restaura el icono en el Escritorio.

### Ejecución Directa por Terminal
```bash
python app.py
```
Abre la aplicación directamente en modo ventana de escritorio (`http://127.0.0.1:5000`).

---

## 🏗️ Arquitectura del Proyecto

```text
Prisma-Converter/
├── app.py                      # Punto de entrada de la aplicación de escritorio
├── Prisma.bat                  # Panel de control y lanzador en 1 clic
├── requirements.txt            # Dependencias locales en Python
├── core/                       # Motores de procesamiento y seguridad
│   ├── converter.py            # Conversor universal de documentos e imágenes
│   ├── pdf_tools.py            # Manipulación de PDFs mediante PyMuPDF
│   ├── audio_processor.py      # Procesamiento y corte de audio
│   ├── video_processor.py      # Conversión y compresión de video con FFmpeg
│   ├── video_downloader.py     # Motor de descargas por enlace con yt-dlp
│   ├── security.py             # Validación CSRF, desinfección y cifrado
│   ├── cleanup.py              # Limpieza automática de archivos temporales
│   └── utils.py                # Utilidades de sistema y gestión de ficheros
├── routes/                     # Blueprints organizados por área
│   ├── views.py                # Vistas principales (Inicio, Conversor, Avanzadas)
│   ├── views_audio.py          # Vistas de Audio y Video
│   ├── converter.py            # Endpoints de la API de conversión
│   ├── pdf.py                  # Endpoints de la API de PDFs
│   ├── audio.py                # Endpoints de la API de Audio
│   ├── video.py                # Endpoints de la API de Video y Descargas
│   ├── file_tools.py           # Compresión, Criptografía y Hojas de Cálculo
│   ├── tools.py                # Código QR y Paleta de Colores
│   └── history.py              # Historial de sesión local
├── static/                     # CSS, JavaScript y recursos gráficos
│   ├── css/                    # Estilos modulares (vars, layout, components)
│   ├── audio/                  # Estilos y scripts de audio y video
│   ├── theme_customizer.js     # Personalizador de temas (10 pares simétricos)
│   ├── i18n.js                 # Diccionario de traducción (ES / PT / EN)
│   └── logo.ico                # Icono de la aplicación
├── templates/                  # Vistas HTML responsivas y modales
└── scripts/                    # Scripts de automatización en Windows
    ├── Iniciar_Prisma.vbs      # Lanzador silencioso (sin ventana de comandos)
    └── criar_atalho.ps1        # Generador del acceso directo en el Escritorio
```

---

## 🔒 Privacidad y Seguridad

* 💻 **Procesamiento 100% Local:** Nada se envía a la nube; tus archivos jamás viajan por la red pública.
* 🗑️ **Depuración Automática:** Ciclo de vida seguro para ficheros temporales con borrado automático.
* 🛡️ **Seguridad Defensiva:** Desinfección contra *Path Traversal*, protección ante *Zip Bombs* y control de tipos MIME.

---

## 📜 Licencia

Distribuido bajo la licencia **GNU General Public License v3.0 (GPLv3)**.  
Consulta el archivo [LICENSE](LICENSE) para más información.
