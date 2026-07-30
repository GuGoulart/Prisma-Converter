# Guía de Instalación y Ejecución Desktop — Windows, macOS y Linux

Esta guía proporciona instrucciones detalladas para instalar, configurar, ejecutar, actualizar y desinstalar **Prisma Converter** en entornos de escritorio.

---

## 🖥️ 1. Windows (10 / 11)

### Requisitos
- **SO:** Windows 10 (64-bit) o Windows 11.
- **Python:** Versión 3.10 o superior.

### Instalación

1. **Instalar Python:**
   - Descargar desde [python.org/downloads](https://www.python.org/downloads/)
   - **IMPORTANTE:** Marcar la casilla **"Add Python to PATH"**.

2. **Clonar repositorio:**
   ```powershell
   git clone https://github.com/GuGoulart/prisma-converter.git
   cd prisma-converter
   ```

3. **Crear entorno virtual:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```

---

## 🍎 2. macOS & 🐧 3. Linux

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y python3 python3-venv python3-pip libreoffice ffmpeg git

# Clonar e iniciar
git clone https://github.com/GuGoulart/prisma-converter.git
cd prisma-converter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
