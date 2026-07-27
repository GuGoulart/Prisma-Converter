import sys, os
sys.path.insert(0, os.path.abspath("."))

from core.media_tools import baixar_midia_url

def progress_cb(pct, status):
    print(f"[{pct:.1f}%] {status}")

print("Testing yt_dlp import and function syntax...")
try:
    import yt_dlp
    print("yt_dlp version:", yt_dlp.__version__)
    print("baixar_midia_url function ready!")
except Exception as e:
    print("Error:", e)
