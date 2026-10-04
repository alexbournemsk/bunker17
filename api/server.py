#!/usr/bin/env python3
"""Таблица рекордов "Бункер 17". Только стандартная библиотека.
Данные лежат в SQLite отдельно от файлов игры, поэтому обновление index.html их не трогает."""
import json, os, re, sqlite3, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.environ.get("B17_DB", "/var/lib/bunker17/scores.db")
PORT = int(os.environ.get("B17_PORT", "8017"))
MAX_SCORE = 200000      # выше этого честным забегом не набрать
MIN_GAP = 10            # секунд между записями с одного адреса
last_post = {}

def db():
    c = sqlite3.connect(DB, timeout=5)
    c.execute("""CREATE TABLE IF NOT EXISTS scores(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, score INTEGER NOT NULL,
        wave INTEGER NOT NULL, win INTEGER NOT NULL, ts INTEGER NOT NULL, ip TEXT)""")
    return c

class H(BaseHTTPRequestHandler):
    def out(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(body)

    def ip(self):
        return self.headers.get("X-Real-IP") or self.client_address[0]

    def do_GET(self):
        if not self.path.split("?")[0].rstrip("/").endswith("/scores"):
            return self.out(404, {"error": "not found"})
        with db() as c:
            rows = c.execute("SELECT name,score,wave,win,ts FROM scores ORDER BY score DESC, ts ASC LIMIT 20").fetchall()
        self.out(200, [dict(name=r[0], score=r[1], wave=r[2], win=bool(r[3]), ts=r[4]) for r in rows])

    def do_POST(self):
        if not self.path.split("?")[0].rstrip("/").endswith("/scores"):
            return self.out(404, {"error": "not found"})
        ip, now = self.ip(), time.time()
        if now - last_post.get(ip, 0) < MIN_GAP:
            return self.out(429, {"error": "слишком часто"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n <= 0 or n > 2000: raise ValueError
            d = json.loads(self.rfile.read(n))
            name = re.sub(r"[\x00-\x1f<>]", "", str(d["name"])).strip()[:16]
            score, wave, win = int(d["score"]), int(d["wave"]), 1 if d.get("win") else 0
            if not name or not (0 <= score <= MAX_SCORE) or not (0 <= wave <= 10): raise ValueError
        except Exception:
            return self.out(400, {"error": "плохие данные"})
        last_post[ip] = now
        with db() as c:
            c.execute("INSERT INTO scores(name,score,wave,win,ts,ip) VALUES(?,?,?,?,?,?)", (name, score, wave, win, int(now), ip))
            place = c.execute("SELECT COUNT(*) FROM scores WHERE score>?", (score,)).fetchone()[0] + 1
        self.out(200, {"ok": True, "place": place})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    db().close()
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
