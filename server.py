#!/usr/bin/env python3
"""简易服务器：数据存储到 SQLite，提供 JSON 数据和前端页面"""
import json
import http.server
import os
import sqlite3
import time

DB_PATH = '/tmp/product_data.db'
API_FILES = [('api1', '/tmp/api1.json'), ('api2', '/tmp/api2.json'),
             ('api3', '/tmp/api3.json'), ('api4', '/tmp/api4.json')]
LOGIN_PWD = 'Shiliang521'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS api_cache (
        name TEXT PRIMARY KEY,
        data TEXT,
        updated_at INTEGER
    )''')
    conn.commit()
    conn.close()

def load_into_db():
    conn = sqlite3.connect(DB_PATH)
    now = int(time.time())
    for name, path in API_FILES:
        try:
            with open(path) as f:
                data = json.load(f)
            conn.execute('INSERT OR REPLACE INTO api_cache (name, data, updated_at) VALUES (?,?,?)',
                         (name, json.dumps(data, ensure_ascii=False), now))
        except Exception as e:
            conn.execute('INSERT OR REPLACE INTO api_cache (name, data, updated_at) VALUES (?,?,?)',
                         (name, json.dumps({"error": str(e)}, ensure_ascii=False), now))
    conn.commit()
    conn.close()

def get_from_db(name):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT data FROM api_cache WHERE name=?', (name,)).fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return {"error": "not found"}

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/'):
            name = self.path.split('/api/')[1].split('?')[0]
            if name == 'refresh':
                load_into_db()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}, ensure_ascii=False).encode('utf-8'))
                return
            data = get_from_db(name)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
        elif self.path == '/' or self.path == '/index.html' or self.path == '/share':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = open(os.path.join(os.path.dirname(__file__), 'index.html'), 'rb').read()
            self.wfile.write(html)
        else:
            super().do_GET()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length else '{}'
        resp = {"ok": False}
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}
        if self.path == '/api/login':
            resp = {"ok": payload.get('password') == LOGIN_PWD}
        elif self.path == '/api/update':
            name = payload.get('name', '')
            data = payload.get('data', {})
            if name in ('api1', 'api2', 'api3', 'api4'):
                conn = sqlite3.connect(DB_PATH)
                conn.execute('INSERT OR REPLACE INTO api_cache (name, data, updated_at) VALUES (?,?,?)',
                             (name, json.dumps(data, ensure_ascii=False), int(time.time())))
                conn.commit()
                conn.close()
                resp = {"ok": True, "name": name}
            else:
                resp = {"ok": False, "error": "invalid name"}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    init_db()
    load_into_db()
    port = 8899
    print(f'Server running at http://localhost:{port}')
    print(f'Data cached in {DB_PATH}')
    http.server.HTTPServer(('0.0.0.0', port), Handler).serve_forever()
