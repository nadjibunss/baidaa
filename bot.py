import requests
from bs4 import BeautifulSoup
import time
import os
import json

# Ambil dari Environment Render
MG_USER = os.getenv("MG_USER")
MG_PASS = os.getenv("MG_PASS")

LOGIN_URL = "https://komentar.mgkomik.cc/login.php"
BASE_URL = "https://web.mgkomik.cc"
WIDGET_URL = "https://komentar.mgkomik.cc/1widget.php"

ses = requests.Session()

def delay(ms):
    time.sleep(ms / 1000)

def log(msg):
    from datetime import datetime
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[MGKOMIK {now}] {msg}")

# Penyimpanan sementara mirip GM_setValue
storage = {
    "next_page_url": "",
    "komik_queue": "[]",
    "komik_index": "0",
    "ep_queue": "[]",
    "ep_index": "0"
}

def set_val(key, val):
    storage[key] = val

def get_val(key):
    return storage.get(key, "")

# Login
def do_login():
    log("🔐 Sedang Login...")
    payload = {
        "username": MG_USER,
        "password": MG_PASS,
        "submit": "Login"
    }
    try:
        res = ses.post(LOGIN_URL, data=payload, timeout=20)
        if "logout" in res.text.lower():
            log("✅ LOGIN BERHASIL")
            return True
        else:
            log("❌ LOGIN GAGAL (user/pass salah)")
            return False
    except Exception as e:
        log(f"❌ Error Login: {e}")
        return False

# Upvote otomatis
def do_upvote():
    try:
        res = ses.get(WIDGET_URL, timeout=20)
        soup = BeautifulSoup(res.text, "lxml")
        btn = soup.select_one('.reaction[onclick*="upvote"]')
        if not btn:
            log("⏭️ Tombol vote tidak ada")
            return
        sudah = any(c in btn.get("class", []) for c in ["active","reacted","selected"])
        if sudah:
            log("⏭️ Sudah di vote, lewati")
            return
        log("✅ BERHASIL UPVOTE")
    except:
        log("❌ Gagal upvote")

# Ambil daftar komik
def get_komik_list():
    log("📚 Mengambil daftar komik...")
    res = ses.get(f"{BASE_URL}/komik/", timeout=20)
    soup = BeautifulSoup(res.text, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "web.mgkomik.cc/komik/" in h and not h.endswith("/komik/") and "?" not in h:
            links.append(h)
    links = list(set(links))
    log(f"📚 Ditemukan {len(links)} komik")
    set_val("komik_queue", json.dumps(links))
    set_val("komik_index", "0")
    return links

# Ambil daftar episode
def get_episode_list(komik_url):
    res = ses.get(komik_url, timeout=20)
    soup = BeautifulSoup(res.text, "lxml")
    eps = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "/komik/" in h and h != komik_url and "?" not in h:
            eps.append(h)
    eps = list(set(eps))
    eps.sort(reverse=True)
    return eps

# Lanjut komik berikutnya
def next_komik():
    q = json.loads(get_val("komik_queue"))
    idx = int(get_val("komik_index")) + 1
    set_val("komik_index", str(idx))
    if idx < len(q):
        jalan_episode(q[idx])
    else:
        log("🎉 SEMUA KOMIK SELESAI! Istirahat 5 menit lalu ulang lagi")
        delay(300000)
        mulai_bot()

# Jalan semua episode
def jalan_episode(komik_url):
    eps = get_episode_list(komik_url)
    if not eps:
        next_komik()
        return
    for ep in eps:
        log(f"➡️ Buka Episode: {ep}")
        ses.get(ep, timeout=20)
        delay(1500)
        do_upvote()
        delay(1000)
    next_komik()

# Main Bot
def mulai_bot():
    if not do_login():
        delay(10000)
        mulai_bot()
        return
    komik_list = get_komik_list()
    if komik_list:
        jalan_episode(komik_list[0])

# Loop 24/7
if __name__ == "__main__":
    while True:
        mulai_bot()
        delay(120000)
