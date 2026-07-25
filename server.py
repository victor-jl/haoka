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
import urllib.request

DB_PATH = '/tmp/product_data.db'
API_FILES = [('api1', '/tmp/api1.json'), ('api2', '/tmp/api2.json'),
             ('api3', '/tmp/api3.json'), ('api4', '/tmp/api4.json')]

# Supabase config (public anon key - RLS allows public read on app_config)
SUPABASE_URL = 'https://rnqrgmaeibwbfeqkjpky.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJucXJnbWFlaWJ3YmZlcWtqcGt5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ5ODQ0MjUsImV4cCI6MjEwMDU2MDQyNX0.QUDGuzcCwpPD2jH8sZ0Kd4wdNGcQKYXwj0EhfRveNME'

# Cached config from Supabase app_config table
_config_cache = {}
_config_cache_time = 0

def get_config(key, default='', max_age=60):
    """Fetch a config value from Supabase app_config table, with caching."""
    global _config_cache, _config_cache_time
    now = time.time()
    if now - _config_cache_time > max_age:
        try:
            req = urllib.request.Request(
                f'{SUPABASE_URL}/rest/v1/app_config?select=key,value',
                headers={
                    'apikey': SUPABASE_ANON_KEY,
                    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
                    'Accept': 'application/json',
                }
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
            _config_cache = {row['key']: row['value'] for row in resp}
            _config_cache_time = now
        except Exception as e:
            print(f"[Config] Failed to fetch from Supabase: {e}")
    # 有缓存时用缓存值，无缓存时返回 default
    return _config_cache.get(key, default)

# Submail SMS config (set via environment variables)
SUBMAIL_APPID = os.environ.get('SUBMAIL_APPID', '')
SUBMAIL_APPKEY = os.environ.get('SUBMAIL_APPKEY', '')
SUBMAIL_PROJECT = os.environ.get('SUBMAIL_PROJECT', '')  # 短信模板ID

def send_sms_code(phone, code):
    """Send verification code via Submail API, fallback to console print."""
    if SUBMAIL_APPID and SUBMAIL_APPKEY and SUBMAIL_PROJECT:
        try:
            data = urllib.parse.urlencode({
                'appid': SUBMAIL_APPID,
                'signature': SUBMAIL_APPKEY,
                'to': phone,
                'project': SUBMAIL_PROJECT,
                'vars': json.dumps({"code": code, "time": "5"}, ensure_ascii=False),
            }).encode()
            req = urllib.request.Request(
                'https://api.submail.cn/message/xsend.json',
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
            if resp.get('status') != 'success':
                print(f"[SMS Warning] Submail send failed: {resp}")
        except Exception as e:
            print(f"[SMS Warning] Submail error: {e}")
    print(f"[SMS Verification] Code for {phone}: {code}")

# In-memory stores for verification codes and sessions
verification_codes = {}  # phone -> {code, expires_at}
sessions = {}  # token -> {phone, is_admin, created_at}
verify_attempts = {}  # ip+phone -> [timestamp, ...]
send_code_limits = {}  # phone -> [timestamp, ...]

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
                now = time.time()
                limits = send_code_limits.get(phone, [])
                limits = [t for t in limits if now - t < 60]
                if len(limits) >= 3:
                    resp = {"ok": False, "error": "发送太频繁，请稍后再试"}
                else:
                    limits.append(now)
                    send_code_limits[phone] = limits
                    code = str(random.randint(100000, 999999))
                    verification_codes[phone] = {'code': code, 'expires_at': now + 300}
                    send_sms_code(phone, code)
                    resp = {"ok": True}
        elif self.path == '/api/verify-code':
            phone = payload.get('phone', '')
            code = payload.get('code', '')
            stored = verification_codes.get(phone)
            now = time.time()
            # Rate limit: max 5 failed attempts in 5min per ip+phone
            client_ip = self.client_address[0]
            attempt_key = client_ip + '|' + phone
            attempts = verify_attempts.get(attempt_key, [])
            attempts = [t for t in attempts if now - t < 300]
            if len(attempts) >= 5:
                resp = {"ok": False, "error": "尝试次数过多，请5分钟后重试"}
            elif not stored:
                resp = {"ok": False, "error": "请先获取验证码"}
            elif now > stored['expires_at']:
                verification_codes.pop(phone, None)
                attempts.append(now)
                verify_attempts[attempt_key] = attempts
                resp = {"ok": False, "error": "验证码已过期"}
            elif stored['code'] != code:
                attempts.append(now)
                verify_attempts[attempt_key] = attempts
                resp = {"ok": False, "error": "验证码错误"}
            elif phone != get_config('admin_phone', ''):
                verification_codes.pop(phone, None)
                attempts.append(now)
                verify_attempts[attempt_key] = attempts
                resp = {"ok": False, "error": "该手机号无登录权限"}
            else:
                verification_codes.pop(phone, None)
                verify_attempts.pop(attempt_key, None)
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
    # Fetch public IP on startup
    public_ip = "unknown"
    try:
        req = urllib.request.Request('https://api.ipify.org', headers={'User-Agent': 'curl/8.0'})
        public_ip = urllib.request.urlopen(req, timeout=5).read().decode().strip()
    except Exception:
        pass
    print(f'Server running at http://localhost:{port}')
    print(f'Public: http://{public_ip}:{port}' if public_ip != 'unknown' else '')
    print(f'Data cached in {DB_PATH}')
    http.server.HTTPServer(('0.0.0.0', port), Handler).serve_forever()
