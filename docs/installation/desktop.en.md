# Desktop Installation and Setup Guide — Windows, macOS & Linux

This guide provides detailed step-by-step instructions to install, configure, run, update, and uninstall **Prisma Converter** on Desktop environments.

---

## 🖥️ 1. Windows (10 / 11)

### Requirements
- **OS:** Windows 10 (64-bit) or Windows 11.
- **Python:** Version 3.10 or higher.
- **Office:** Microsoft Office installed (optional, for maximum conversion fidelity) or LibreOffice.

### Installation Steps

1. **Install Python:**
   - Download from [python.org/downloads](https://www.python.org/downloads/)
   - **IMPORTANT:** Check **"Add Python to PATH"** during installation.

2. **Clone Repository:**
   ```powershell
   git clone https://github.com/GuGoulart/prisma-converter.git
   cd prisma-converter
   ```

3. **Set up Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. **Install Dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables:**
   - Create `.env` file in the root directory:
     ```env
     FLASK_ENV=development
     SECRET_KEY=your_secure_random_key_here
     ```

6. **Run Application:**
   ```powershell
   python app.py
   ```
   - Open browser at `http://127.0.0.1:5000`

---

## 🍎 2. macOS (Intel / Apple Silicon)

```bash
# Install system packages via Homebrew
brew install python@3.10 libreoffice ffmpeg

# Clone & setup
git clone https://github.com/GuGoulart/prisma-converter.git
cd prisma-converter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## 🐧 3. Linux (Ubuntu / Debian / Fedora)

```bash
# Install prerequisites on Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-venv python3-pip libreoffice ffmpeg git

# Setup & Run
git clone https://github.com/GuGoulart/prisma-converter.git
cd prisma-converter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
