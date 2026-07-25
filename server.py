#!/usr/bin/env python3
"""简易服务器：数据存储到 SQLite，提供 JSON 数据和前端页面"""
import json
import http.server
import os
import random
import re
import secrets
import shlex
import sqlite3
import subprocess
import time
import urllib.parse

DB_PATH = '/tmp/product_data.db'
API_FILES = [('api1', '/tmp/api1.json'), ('api2', '/tmp/api2.json'),
             ('api3', '/tmp/api3.json'), ('api4', '/tmp/api4.json')]
ADMIN_PHONE = '17602111723'

# In-memory stores for verification codes and sessions
verification_codes = {}  # phone -> {code, expires_at}
sessions = {}  # token -> {phone, is_admin, created_at}

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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, phone')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/'):
            name = self.path.split('/api/')[1].split('?')[0]
            if name == 'check-session':
                qs = urllib.parse.parse_qs(self.path.split('?')[1]) if '?' in self.path else {}
                token = (qs.get('token') or [''])[0]
                session = sessions.get(token)
                resp = {"ok": bool(session)}
                if session:
                    resp['is_admin'] = session['is_admin']
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                return
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
            self.send_response(404)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "not found"}, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length else '{}'
        resp = {"ok": False}
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}
        if self.path == '/api/send-code':
            phone = payload.get('phone', '')
            if not re.match(r'^1\d{10}$', phone):
                resp = {"ok": False, "error": "invalid phone"}
            else:
                code = str(random.randint(100000, 999999))
                verification_codes[phone] = {'code': code, 'expires_at': time.time() + 300}
                print(f"[SMS Verification] Code for {phone}: {code}")
                resp = {"ok": True}
        elif self.path == '/api/verify-code':
            phone = payload.get('phone', '')
            code = payload.get('code', '')
            stored = verification_codes.get(phone)
            if not stored:
                resp = {"ok": False, "error": "请先获取验证码"}
            elif time.time() > stored['expires_at']:
                verification_codes.pop(phone, None)
                resp = {"ok": False, "error": "验证码已过期"}
            elif stored['code'] != code:
                resp = {"ok": False, "error": "验证码错误"}
            elif phone != ADMIN_PHONE:
                verification_codes.pop(phone, None)
                resp = {"ok": False, "error": "该手机号无登录权限"}
            else:
                verification_codes.pop(phone, None)
                token = secrets.token_hex(32)
                sessions[token] = {'phone': phone, 'is_admin': True, 'created_at': time.time()}
                resp = {"ok": True, "token": token, "is_admin": True}
        elif self.path == '/api/logout':
            token = payload.get('token', '')
            sessions.pop(token, None)
            resp = {"ok": True}
        elif self.path == '/api/update':
            name = payload.get('name', '')
            curl_cmd = payload.get('curl', '')
            phone = payload.get('phone', '') or self.headers.get('phone', '')
            if not phone or not re.match(r'^1\d{10}$', phone):
                resp = {"ok": False, "error": "invalid or missing phone"}
            elif name not in ('api1', 'api2', 'api3', 'api4'):
                resp = {"ok": False, "error": "invalid name"}
            elif not curl_cmd:
                resp = {"ok": False, "error": "curl required"}
            else:
                if phone:
                    curl_cmd = curl_cmd.replace('{phone}', phone)
                if not re.match(r'^[a-zA-Z0-9\s\-_.:/?#\[\]@!$&\'\"()+,;=%]+$', curl_cmd):
                    resp = {"ok": False, "error": "curl contains unsafe characters"}
                else:
                    try:
                        result = subprocess.run(shlex.split(curl_cmd), shell=False, capture_output=True, text=True, timeout=60)
                        if result.returncode != 0:
                            resp = {"ok": False, "error": "curl failed: " + (result.stderr or result.stdout)[:200]}
                        else:
                            data = json.loads(result.stdout)
                            conn = sqlite3.connect(DB_PATH)
                            conn.execute('INSERT OR REPLACE INTO api_cache (name, data, updated_at) VALUES (?,?,?)',
                                         (name, json.dumps(data, ensure_ascii=False), int(time.time())))
                            conn.commit()
                            conn.close()
                            resp = {"ok": True, "name": name}
                    except json.JSONDecodeError:
                        resp = {"ok": False, "error": "response not valid JSON"}
                    except subprocess.TimeoutExpired:
                        resp = {"ok": False, "error": "curl timeout (60s)"}
                    except Exception as e:
                        resp = {"ok": False, "error": str(e)[:200]}
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "not found"}, ensure_ascii=False).encode('utf-8'))
            return
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
