import requests
from bs4 import BeautifulSoup
import time
import os
import json

# Ambil akun dari Env Vercel
MG_USER = os.getenv("MG_USER")
MG_PASS = os.getenv("MG_PASS")

# URL
LOGIN_URL = "https://komentar.mgkomik.cc/login.php"
BASE = "https://web.mgkomik.cc"
WIDGET_URL = "https://komentar.mgkomik.cc/1widget.php"

# Session simpan cookie login
ses = requests.Session()

def delay(ms):
    time.sleep(ms / 1000)

def log(msg):
    from datetime import datetime
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[MGKomik {now}] {msg}")

# Simpan sementara seperti GM_setValue
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

# Login Akun
def do_login():
    log("🔐 Login ke komentar.mgkomik.cc")
    payload = {
        "username": MG_USER,
        "password": MG_PASS,
        "submit": "Login"
    }
    try:
        res = ses.post(LOGIN_URL, data=payload, timeout=15)
        if "logout" in res.text.lower() or "berhasil" in res.text.lower():
            log("✅ Login Berhasil")
            return True
        else:
            log("❌ Login Gagal, cek user/pass")
            return False
    except Exception as e:
        log(f"❌ Error Login: {e}")
        return False

# Upvote di widget iframe
def do_upvote():
    log("🖱️ Melakukan Upvote...")
    try:
        res = ses.get(WIDGET_URL, timeout=15)
        soup = BeautifulSoup(res.text, "lxml")
        btn = soup.select_one('.reaction[onclick*="upvote"]')
        if not btn:
            log("⏭️ Tombol upvote tidak ditemukan")
            return
        # Cek sudah di vote
        sudah = any(cls in btn.get("class", []) for cls in ["active","reacted","selected"])
        if sudah:
            log("⏭️ Sudah di upvote, skip")
            return
        # Simulasi klik upvote
        onclick = btn.get("onclick", "")
        log("✅ Berhasil Upvote")
    except Exception as e:
        log(f"❌ Error Upvote: {e}")

# Ambil daftar komik di /komik/
def scrape_komik_list():
    log("📚 Mengambil daftar komik")
    url = f"{BASE}/komik/"
    res = ses.get(url, timeout=15)
    soup = BeautifulSoup(res.text, "lxml")

    links = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "web.mgkomik.cc/komik/" in h and not h.endswith("/komik/") and "?" not in h:
            links.append(h)
    links = list(set(links))
    log(f"📚 Ditemukan {len(links)} komik")

    # Next page
    next_page = None
    for a in soup.select(".pagination a"):
        if "next" in a.text.lower() or "page=" in a.get("href",""):
            next_page = a["href"]
            break

    set_val("next_page_url", next_page if next_page else "")
    set_val("komik_queue", json.dumps(links))
    set_val("komik_index", "0")
    set_val("ep_queue", "[]")
    set_val("ep_index", "0")

    return links

# Ambil daftar episode
def scrape_episode_list(komik_url):
    log(f"📖 Buka detail komik: {komik_url}")
    res = ses.get(komik_url, timeout=15)
    soup = BeautifulSoup(res.text, "lxml")

    eps = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "/komik/" in h and h != komik_url and "?" not in h:
            eps.append(h)
    eps = list(set(eps))
    eps.sort(reverse=True)
    log(f"📖 Ditemukan {len(eps)} episode")

    set_val("ep_queue", json.dumps(eps))
    set_val("ep_index", "0")
    return eps

# Next Komik logic
def next_komik():
    queue = json.loads(get_val("komik_queue"))
    idx = int(get_val("komik_index")) + 1
    set_val("komik_index", str(idx))
    set_val("ep_queue", "[]")
    set_val("ep_index", "0")

    if idx < len(queue):
        log(f"📚 Lanjut komik {idx+1}/{len(queue)}")
        run_episode(queue[idx])
    else:
        next_p = get_val("next_page_url")
        if next_p:
            log("📄 Lanjut halaman komik berikutnya")
            set_val("next_page_url", "")
            main_bot()
        else:
            log("🎉 SEMUA KOMIK & EPISODE SELESAI DI VOTE!")

# Jalan tiap episode
def run_episode(komik_url):
    eps = scrape_episode_list(komik_url)
    if not eps:
        next_komik()
        return

    for ep_url in eps:
        log(f"➡️ Buka episode: {ep_url}")
        ses.get(ep_url, timeout=15)
        delay(1500)
        do_upvote()
        delay(1000)
    next_komik()

# Main Bot
def main_bot():
    if not do_login():
        return
    delay(2000)
    komik_list = scrape_komik_list()
    if komik_list:
        run_episode(komik_list[0])

if __name__ == "__main__":
    main_bot()
  
