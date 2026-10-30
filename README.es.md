<div align="center">

# 💎 PRISMA CONVERTER

### **Aplicación de escritorio local para convertir, editar y proteger archivos**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%AAs-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/Frontend-TypeScript-3178C6.svg?style=flat-square&logo=typescript&logoColor=white)](frontend/)
[![Licencia: GPL v3](https://img.shields.io/badge/Licencia-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

</div>

---

## Acerca de

Prisma se ejecuta en su computadora y se abre en su propia ventana. Sus archivos se procesan localmente y no se envían a ningún servidor. Las únicas conexiones externas son las que usted solicita: descargar un video desde un enlace y descargar el modelo de transcripción una sola vez.

## Funciones

| Área | Herramientas |
|---|---|
| **Convertidor** | PDF, DOCX, XLSX, CSV, JSON, PPT, PPTX, PNG, JPG, WEBP y HEIC, con vista previa |
| **PDF** | Combinar, dividir, proteger, desproteger, comprimir, marca de agua, extraer imágenes, eliminar y girar páginas |
| **Audio** | Convertir, cortar, unir, ajustar volumen, normalizar, cambiar velocidad, invertir y transcribir |
| **Video** | Convertir, comprimir, extraer MP3, crear GIF, quitar audio, capturar un fotograma y descargar desde un enlace |
| **Archivos** | ZIP y TAR.GZ, ZIP con contraseña, cifrado AES-256, hash, renombrar en lote, combinar hojas de cálculo |
| **Imágenes** | Generar y leer códigos QR, extraer paletas de colores |

Cada tarea muestra su progreso, se puede cancelar y entra en una cola, sin bloquear el resto de la aplicación. Los resultados quedan en el historial y se eliminan según la política elegida: 5 minutos, 15 minutos o justo después de la descarga.

### Qué necesita programas externos

La aplicación detecta lo que está instalado y muestra solo las conversiones posibles.

| Función | Requisito |
|---|---|
| Audio y video | [FFmpeg](https://ffmpeg.org/download.html). Si no está en el PATH, Prisma intenta descargar una copia automáticamente |
| DOCX, PPT y PPTX como origen; hojas de cálculo a PDF o imagen | Microsoft Office **o** [LibreOffice](https://www.libreoffice.org/download/) |
| Texto de imágenes y PDF escaneados (OCR) | [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) |

## Inicio rápido en Windows

Requisito: [Python 3.11 o superior](https://www.python.org/downloads/).

```bash
git clone https://github.com/GuGoulart/Prisma-Converter.git
```

Después, haga doble clic en `Prisma.bat` y elija **[1] Iniciar**. La primera vez instala las dependencias en un entorno propio (`venv`) y crea un acceso directo en el Escritorio.

El servidor se cierra solo unos minutos después de cerrar la última ventana, siempre que no haya tareas en curso.

## Desarrollo

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
npm install

npm run watch         # recompila el frontend al guardar
python app.py

python -m pytest tests   # pruebas del backend
npm run typecheck        # verificación de tipos
npm run e2e              # pruebas en navegador real
```

El frontend está en `frontend/` y se compila en `static/dist/`, que está versionado: **ejecutar la aplicación no requiere Node.js**. Ejecute `npm run build` antes de confirmar cambios en el frontend.

Para actualizar dependencias, edite `requirements.in` y genere de nuevo `requirements.txt` en un entorno limpio.

## Privacidad y seguridad

- **Procesamiento local:** el servidor escucha solo en `127.0.0.1` y las páginas no cargan recursos externos.
- **Protección contra otros sitios:** validación de `Host` y `Origin`, token CSRF obligatorio y una política de seguridad de contenido (CSP) sin scripts en línea.
- **Aislamiento:** las descargas se hacen solo por ID de tarea. Los nombres y parámetros enviados nunca se convierten en rutas de disco.
- **Macros deshabilitadas** al abrir documentos con Office.
- **Eliminación:** los archivos se eliminan a través del sistema de archivos. No es una destrucción forense, que no se puede garantizar en SSD.

## Licencia

Distribuido bajo la licencia **GNU General Public License v3.0**. Consulte [LICENSE](LICENSE).
