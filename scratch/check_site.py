import time
import urllib.request
import sys

url = "https://prisma-app.duckdns.org"
print(f"Iniciando verificacao de {url}...")

for attempt in range(1, 20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[ONLINE] Tentativa {attempt}! Status: {resp.status} {resp.reason}")
            sys.exit(0)
    except Exception as e:
        print(f"[*] Tentativa {attempt}/20: {e}")
        time.sleep(15)

print("Ainda processando...")
