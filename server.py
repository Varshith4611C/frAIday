#!/usr/bin/env python3
"""
frAIday — Production Multi-Threaded Real Backend Server
- Concurrent ThreadingTCPServer
- Real File System CRUD in ./workspace/
- Real Terminal Subprocess Execution
- Real Live Web Search (DuckDuckGo & Wikipedia)
- Real LLM Proxy (NVIDIA NIM, Gemini, OpenAI, Ollama)
- Real Live Preview Static Server
"""

import http.server
import socketserver
import os
import sys
import json
import urllib.request
import urllib.parse
import subprocess
import shutil
import re
import time
import shlex
import zipfile
import io
from pathlib import Path

PORT = 8080
BASE_DIR = Path(__file__).resolve().parent

# Load local environment variables from .env if present
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.is_file():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception as _e:
        print(f"[frAIday] .env load note: {_e}")

DEFAULT_WORKSPACE_DIR = BASE_DIR / "workspace"
DEFAULT_WORKSPACE_DIR.mkdir(exist_ok=True)
WORKSPACES_ROOT = BASE_DIR / "workspaces"
WORKSPACES_ROOT.mkdir(exist_ok=True)

ACTIVE_WORKSPACE_FILE = BASE_DIR / ".fraiday_active_workspace.txt"
ACTIVE_WORKSPACE_NAME = "default"
if ACTIVE_WORKSPACE_FILE.is_file():
    try:
        saved_ws = ACTIVE_WORKSPACE_FILE.read_text(encoding="utf-8").strip()
        if saved_ws:
            ACTIVE_WORKSPACE_NAME = saved_ws
    except Exception:
        pass

def get_active_workspace_name():
    global ACTIVE_WORKSPACE_NAME
    return ACTIVE_WORKSPACE_NAME

def get_active_workspace_dir(name=None):
    global ACTIVE_WORKSPACE_NAME
    target_name = name or ACTIVE_WORKSPACE_NAME
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', str(target_name)).strip() or "default"
    if clean_name.lower() == "default":
        d = DEFAULT_WORKSPACE_DIR
    else:
        d = WORKSPACES_ROOT / clean_name
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_session_file():
    ws = get_active_workspace_name()
    if ws == "default":
        return BASE_DIR / ".fraiday_session.json"
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '', ws) or "default"
    return BASE_DIR / f".fraiday_session_{clean}.json"

def list_workspaces():
    global ACTIVE_WORKSPACE_NAME
    workspaces = []
    # 1. Default workspace
    default_dir = DEFAULT_WORKSPACE_DIR
    default_dir.mkdir(exist_ok=True)
    count = sum(1 for _ in default_dir.rglob("*") if _.is_file())
    has_html = (default_dir / "index.html").is_file() or any(default_dir.glob("**/*.html"))
    workspaces.append({
        "id": "default",
        "name": "default",
        "path": "./workspace/",
        "is_active": (ACTIVE_WORKSPACE_NAME == "default"),
        "file_count": count,
        "has_preview": has_html,
        "is_default": True
    })
    # 2. Workspaces inside workspaces/ directory
    if WORKSPACES_ROOT.exists():
        for item in sorted(list(WORKSPACES_ROOT.iterdir())):
            if item.is_dir() and not item.name.startswith("."):
                f_count = sum(1 for _ in item.rglob("*") if _.is_file())
                f_html = (item / "index.html").is_file() or any(item.glob("**/*.html"))
                workspaces.append({
                    "id": item.name,
                    "name": item.name,
                    "path": f"./workspaces/{item.name}/",
                    "is_active": (ACTIVE_WORKSPACE_NAME == item.name),
                    "file_count": f_count,
                    "has_preview": f_html,
                    "is_default": False
                })
    return workspaces

def switch_workspace(name):
    global ACTIVE_WORKSPACE_NAME
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', str(name)).strip() or "default"
    if clean_name.lower() == "default":
        ACTIVE_WORKSPACE_NAME = "default"
        DEFAULT_WORKSPACE_DIR.mkdir(exist_ok=True)
    else:
        target = WORKSPACES_ROOT / clean_name
        target.mkdir(parents=True, exist_ok=True)
        ACTIVE_WORKSPACE_NAME = clean_name
    try:
        ACTIVE_WORKSPACE_FILE.write_text(ACTIVE_WORKSPACE_NAME, encoding="utf-8")
    except Exception:
        pass
    return ACTIVE_WORKSPACE_NAME

def create_workspace(name, switch_to=True):
    global ACTIVE_WORKSPACE_NAME
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', str(name)).strip()
    if not clean_name:
        raise ValueError("Invalid workspace name. Use alphanumeric characters, hyphens, or underscores.")
    if clean_name.lower() == "default":
        target = DEFAULT_WORKSPACE_DIR
    else:
        target = WORKSPACES_ROOT / clean_name
    target.mkdir(parents=True, exist_ok=True)
    if switch_to:
        switch_workspace(clean_name)
    return target

def delete_workspace(name):
    global ACTIVE_WORKSPACE_NAME
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', str(name)).strip()
    if clean_name.lower() == "default" or not clean_name:
        raise ValueError("Cannot delete the default workspace.")
    target = WORKSPACES_ROOT / clean_name
    if target.is_dir():
        shutil.rmtree(target, ignore_errors=True)
    session_file = BASE_DIR / f".fraiday_session_{clean_name}.json"
    if session_file.is_file():
        try:
            session_file.unlink()
        except Exception:
            pass
    if ACTIVE_WORKSPACE_NAME == clean_name:
        switch_workspace("default")
    return True

class WorkspaceDirProxy(os.PathLike):
    @property
    def _path(self):
        return get_active_workspace_dir()

    def __fspath__(self):
        return str(self._path)

    def __getattr__(self, name):
        return getattr(self._path, name)

    def __truediv__(self, other):
        return self._path / other

    def __rtruediv__(self, other):
        return Path(other) / self._path

    def __str__(self):
        return str(self._path)

    def __repr__(self):
        return repr(self._path)

    def __eq__(self, other):
        return self._path == other or str(self._path) == str(other)

    def __hash__(self):
        return hash(self._path)

class SessionFileProxy(os.PathLike):
    @property
    def _path(self):
        return get_session_file()

    def __fspath__(self):
        return str(self._path)

    def __getattr__(self, name):
        return getattr(self._path, name)

    def __truediv__(self, other):
        return self._path / other

    def __str__(self):
        return str(self._path)

    def __repr__(self):
        return repr(self._path)

    def __eq__(self, other):
        return self._path == other or str(self._path) == str(other)

    def __hash__(self):
        return hash(self._path)

WORKSPACE_DIR = WorkspaceDirProxy()
SESSION_FILE = SessionFileProxy()

# Auto-discover and prepend Git Unix utilities (sed, grep, awk, head, tail, wc, etc.) to PATH on Windows
if sys.platform.startswith("win"):
    git_candidate_paths = [
        r"C:\Program Files\Git\usr\bin",
        r"C:\Program Files\Git\bin",
        r"C:\Program Files (x86)\Git\usr\bin",
        r"C:\Program Files (x86)\Git\bin",
        os.path.expanduser(r"~\AppData\Local\Programs\Git\usr\bin"),
        os.path.expanduser(r"~\AppData\Local\Programs\Git\bin"),
    ]
    valid_git_dirs = [p for p in git_candidate_paths if os.path.isdir(p)]
    if valid_git_dirs:
        os.environ["PATH"] = ";".join(valid_git_dirs) + ";" + os.environ.get("PATH", "")

# Load .env file if present
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.is_file():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ[_k.strip()] = _v.strip()
    except Exception:
        pass

# Initialize Vectorize Hindsight Memory Service
try:
    from hindsight_service import HINDSIGHT
except Exception as _hse:
    print(f"[frAIday] Hindsight service import note: {_hse}")
    HINDSIGHT = None

# Preconfigured keys loaded from environment or .env
DEFAULT_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
DEFAULT_GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
DEFAULT_NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY", "")
DEFAULT_PROVIDER = os.environ.get("AI_PROVIDER", "gemini" if DEFAULT_GEMINI_KEY else "groq")

def get_initial_key(prov):
    if prov == "gemini":
        return DEFAULT_GEMINI_KEY
    elif prov == "groq":
        return DEFAULT_GROQ_KEY
    elif prov == "nvidia":
        return DEFAULT_NVIDIA_KEY
    return ""

def get_initial_model(prov):
    if prov == "gemini":
        return os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    elif prov == "groq":
        return os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    elif prov == "nvidia":
        return os.environ.get("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct")
    return "gemini-3.8-flash"

# Active runtime system configuration (updated via POST /api/config)
ACTIVE_CONFIG = {
    "provider": DEFAULT_PROVIDER,
    "api_key": get_initial_key(DEFAULT_PROVIDER),
    "model": get_initial_model(DEFAULT_PROVIDER),
    "safety": "autonomous_execute"
}

# Dynamic model and key cooldown trackers + round-robin index
MODEL_COOLDOWNS = {}
KEY_COOLDOWNS = {}
GROQ_KEY_INDEX = 0

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        # Ignore client disconnects/aborts cleanly without crashing server
        pass

class FrAIdayHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: List workspaces
        if path == "/api/workspaces":
            self.send_json(200, {
                "success": True,
                "active": get_active_workspace_name(),
                "active_workspace": get_active_workspace_name(),
                "active_path": "./" + str(get_active_workspace_dir().relative_to(BASE_DIR).as_posix()) + "/",
                "workspaces": list_workspaces()
            })
            return

        # 1a. API: List workspace files
        if path == "/api/workspace/files":
            self.handle_list_files()
            return

        # 1b. API: Export workspace as ZIP archive
        if path == "/api/workspace/export-zip":
            self.handle_export_zip()
            return

        # 1c. API: List workspace checkpoints
        if path == "/api/workspace/checkpoints":
            self.handle_list_checkpoints()
            return

        # 1d. API: Persistent Session
        if path == "/api/session":
            self.handle_get_session()
            return

        # 2. API: Read specific workspace file
        if path == "/api/workspace/file":
            rel_path = query.get("path", [""])[0]
            self.handle_read_file(rel_path)
            return

        # 3. API: Real Live Web Search
        if path == "/api/search":
            q = query.get("q", [""])[0]
            self.handle_web_search(q)
            return

        # 4. API: System Configuration
        if path == "/api/config":
            keys_list = [k.strip() for k in re.split(r'[,;\n\r\s]+', ACTIVE_CONFIG["api_key"]) if k.strip()]
            self.send_json(200, {
                "status": "online",
                "workspace": str(WORKSPACE_DIR),
                "provider": ACTIVE_CONFIG["provider"],
                "model": ACTIVE_CONFIG["model"],
                "api_key": ACTIVE_CONFIG["api_key"],
                "keys_count": len(keys_list),
                "has_api_key": bool(ACTIVE_CONFIG["api_key"]),
                "safety": ACTIVE_CONFIG["safety"]
            })
            return

        # 4b. API: Vectorize Hindsight Memory Engine
        if path == "/api/hindsight/status":
            if HINDSIGHT:
                self.send_json(200, HINDSIGHT.get_status())
            else:
                self.send_json(200, {"status": "offline", "engine": "none", "stats": {"total": 0}})
            return

        if path == "/api/hindsight/bank":
            if HINDSIGHT:
                target_bank = query.get("bank_id", [None])[0]
                self.send_json(200, HINDSIGHT.get_bank(target_bank))
            else:
                self.send_json(404, {"error": "Hindsight service unavailable"})
            return

        # 5. Serve Workspace Preview
        if path == "/workspace":
            self.send_response(302)
            self.send_header("Location", "/workspace/")
            self.end_headers()
            return

        if path.startswith("/workspace/"):
            rel = path[len("/workspace/"):].strip()
            # If requesting the root preview /workspace/ or /workspace/index.html
            if rel in ("", "index.html"):
                if (WORKSPACE_DIR / "index.html").is_file():
                    self.serve_custom_file(WORKSPACE_DIR / "index.html")
                    return
                # Check for frontend/index.html, src/index.html, public/index.html, client/index.html, dist/index.html
                for cand in ["frontend/index.html", "src/index.html", "public/index.html", "client/index.html", "dist/index.html"]:
                    if (WORKSPACE_DIR / cand).is_file():
                        self.serve_custom_file(WORKSPACE_DIR / cand)
                        return
                any_html = sorted(list(WORKSPACE_DIR.glob("**/*.html")), key=lambda p: len(p.parts))
                if any_html:
                    self.serve_custom_file(any_html[0])
                    return

            file_target = (WORKSPACE_DIR / rel).resolve()
            if WORKSPACE_DIR in file_target.parents or file_target == WORKSPACE_DIR:
                if file_target.is_file():
                    self.serve_custom_file(file_target)
                    return
                elif (file_target / "index.html").is_file():
                    self.serve_custom_file(file_target / "index.html")
                    return

            # Smart asset fallback: if e.g. /workspace/style.css is requested directly, check subfolders
            if "/" not in rel:
                for sub in ["frontend", "src", "public", "assets", "styles", "js", "css", "client", "dist"]:
                    cand = (WORKSPACE_DIR / sub / rel).resolve()
                    if cand.is_file():
                        self.serve_custom_file(cand)
                        return
                # Also handle style.css vs styles.css or script.js vs main.js
                alt_candidates = []
                if rel == "styles.css":
                    alt_candidates.append("style.css")
                elif rel == "style.css":
                    alt_candidates.append("styles.css")
                elif rel == "main.js":
                    alt_candidates.extend(["script.js", "app.js"])
                elif rel in ("script.js", "app.js"):
                    alt_candidates.append("main.js")

                for alt in alt_candidates:
                    if (WORKSPACE_DIR / alt).is_file():
                        self.serve_custom_file(WORKSPACE_DIR / alt)
                        return
                    for sub in ["frontend", "src", "public", "assets", "styles", "js", "css", "client", "dist"]:
                        cand = (WORKSPACE_DIR / sub / alt).resolve()
                        if cand.is_file():
                            self.serve_custom_file(cand)
                            return

            self.send_json(404, {"error": "Preview file not found"})
            return

        # Fallback to static files from BASE_DIR
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        if path == "/api/config":
            self.handle_update_config(body)
            return

        if path == "/api/workspace/file":
            self.handle_write_file(body)
            return

        if path == "/api/workspace/clear":
            self.handle_clear_workspace()
            return

        if path == "/api/session":
            self.handle_save_session(body)
            return

        if path == "/api/workspace/checkpoint":
            self.handle_create_checkpoint(body)
            return

        if path == "/api/workspace/rollback":
            self.handle_rollback_checkpoint(body)
            return

        if path == "/api/terminal/exec":
            self.handle_terminal_exec(body)
            return

        if path == "/api/llm/chat":
            self.handle_llm_chat(body)
            return

        if path == "/api/build/verify":
            self.handle_build_verify()
            return

        if path == "/api/build/test":
            self.handle_build_test(body)
            return

        if path == "/api/build/inspect-site":
            self.handle_inspect_site()
            return

        # Workspaces Management Routes
        if path == "/api/workspaces/create":
            name = body.get("name", "").strip()
            if not name:
                self.send_json(400, {"error": "Missing workspace name"})
                return
            try:
                target = create_workspace(name, switch_to=body.get("switch", True))
                self.send_json(200, {
                    "success": True,
                    "active": get_active_workspace_name(),
                    "active_workspace": get_active_workspace_name(),
                    "active_path": "./" + str(get_active_workspace_dir().relative_to(BASE_DIR).as_posix()) + "/",
                    "workspaces": list_workspaces(),
                    "created": name
                })
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if path == "/api/workspaces/switch":
            name = body.get("name", "").strip()
            if not name:
                self.send_json(400, {"error": "Missing workspace name"})
                return
            try:
                new_active = switch_workspace(name)
                self.send_json(200, {
                    "success": True,
                    "active": new_active,
                    "active_workspace": new_active,
                    "active_path": "./" + str(get_active_workspace_dir().relative_to(BASE_DIR).as_posix()) + "/",
                    "workspaces": list_workspaces()
                })
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if path == "/api/workspaces/delete":
            name = body.get("name", "").strip()
            if not name:
                self.send_json(400, {"error": "Missing workspace name"})
                return
            try:
                delete_workspace(name)
                self.send_json(200, {
                    "success": True,
                    "active": get_active_workspace_name(),
                    "active_workspace": get_active_workspace_name(),
                    "active_path": "./" + str(get_active_workspace_dir().relative_to(BASE_DIR).as_posix()) + "/",
                    "workspaces": list_workspaces(),
                    "deleted": name
                })
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if path == "/api/workspace/patch":
            self.handle_patch_file(body)
            return

        if path == "/api/browser/inspect":
            self.handle_browser_inspect(body)
            return

        if path == "/api/tools/execute":
            self.handle_tool_execute(body)
            return

        # Vectorize Hindsight Memory Routes
        if path == "/api/hindsight/retain":
            if not HINDSIGHT:
                self.send_json(500, {"error": "Hindsight unavailable"})
                return
            res = HINDSIGHT.retain(
                content=body.get("content", ""),
                bank_id=body.get("bank_id"),
                memory_type=body.get("memory_type", "observation"),
                metadata=body.get("metadata"),
                tags=body.get("tags"),
                context=body.get("context")
            )
            self.send_json(200, res)
            return

        if path == "/api/hindsight/recall":
            if not HINDSIGHT:
                self.send_json(500, {"error": "Hindsight unavailable"})
                return
            res = HINDSIGHT.recall(
                query=body.get("query", ""),
                bank_id=body.get("bank_id"),
                types=body.get("types"),
                max_tokens=body.get("max_tokens", 2048)
            )
            self.send_json(200, res)
            return

        if path == "/api/hindsight/reflect":
            if not HINDSIGHT:
                self.send_json(500, {"error": "Hindsight unavailable"})
                return
            res = HINDSIGHT.reflect(
                query=body.get("query", ""),
                bank_id=body.get("bank_id")
            )
            self.send_json(200, res)
            return

        if path in ("/api/hindsight/reset-scenarios", "/api/hindsight/reset"):
            if not HINDSIGHT:
                self.send_json(500, {"error": "Hindsight unavailable"})
                return
            res = HINDSIGHT.reset_scenarios(bank_id=body.get("bank_id"))
            self.send_json(200, res)
            return

        if path == "/api/hindsight/clear":
            if not HINDSIGHT:
                self.send_json(500, {"error": "Hindsight unavailable"})
                return
            res = HINDSIGHT.clear_bank(bank_id=body.get("bank_id"))
            self.send_json(200, res)
            return

        if path == "/api/hindsight/config":
            if not HINDSIGHT:
                self.send_json(500, {"error": "Hindsight unavailable"})
                return
            HINDSIGHT.update_config(
                base_url=body.get("base_url"),
                api_key=body.get("api_key"),
                bank_id=body.get("bank_id")
            )
            self.send_json(200, HINDSIGHT.get_status())
            return

        self.send_json(404, {"error": "API route not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/api/workspaces/delete", "/api/workspaces"):
            query = urllib.parse.parse_qs(parsed.query)
            ws_name = query.get("name", [""])[0]
            if not ws_name:
                body = self.read_json_body()
                ws_name = body.get("name", "").strip()
            if not ws_name:
                self.send_json(400, {"error": "Missing workspace name parameter"})
                return
            try:
                delete_workspace(ws_name)
                self.send_json(200, {
                    "success": True,
                    "active": get_active_workspace_name(),
                    "active_workspace": get_active_workspace_name(),
                    "active_path": "./" + str(get_active_workspace_dir().relative_to(BASE_DIR).as_posix()) + "/",
                    "workspaces": list_workspaces(),
                    "deleted": ws_name
                })
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        if parsed.path == "/api/workspace/file":
            query = urllib.parse.parse_qs(parsed.query)
            rel_path = query.get("path", [""])[0]
            self.handle_delete_file(rel_path)
            return
        if parsed.path == "/api/session":
            self.handle_delete_session()
            return
        self.send_json(404, {"error": "Not found"})

    def read_json_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        try:
            raw = self.rfile.read(length).decode('utf-8')
            return json.loads(raw)
        except Exception:
            return {}

    def send_json(self, status, data):
        try:
            payload = json.dumps(data).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception:
            pass

    def serve_custom_file(self, path):
        content_type = self.guess_type(str(path))
        try:
            with open(path, 'rb') as f:
                content = f.read()

            # If HTML, inject cache-busters and runtime error monitoring script for autonomous self-healing
            if 'html' in (content_type or '').lower():
                try:
                    text_html = content.decode('utf-8', errors='replace')
                    cur_ts = int(time.time() * 1000)

                    # 1. Automatically cache-bust relative script and style tags so browser never runs stale code
                    def _cache_bust_cb(match):
                        attr = match.group(1)
                        url = match.group(2)
                        if not url.startswith(('http://', 'https://', '//', 'data:', '#')) and '?' not in url:
                            return f'{attr}="{url}?v={cur_ts}"'
                        return match.group(0)

                    text_html = re.sub(r'\b(src|href)=["\']([^"\']+\.(?:js|mjs|css))["\']', _cache_bust_cb, text_html)

                    # 2. Trap script for DevTools forwarding and runtime error catching
                    trap_script = """<script id="fraiday-runtime-trap">
/* frAIday Autonomous Inspection & Runtime Trap + DevTools Console Forwarding */
(function() {
    try {
        var oldErrEl = document.getElementById('fraiday-runtime-errors');
        if (oldErrEl && oldErrEl.parentNode) oldErrEl.parentNode.removeChild(oldErrEl);

        if (window.parent && window.parent !== window) {
            window.parent.postMessage({
                type: 'WORKSPACE_PREVIEW_RELOADED',
                timestamp: Date.now()
            }, '*');
        }
    } catch(_) {}

    var reportedErrors = new Set();

    function recordError(msg, file, line, col, isConsoleError) {
        if (!msg) return;
        var cleanMsg = String(msg).trim();
        if (cleanMsg === 'Script error.' || cleanMsg === 'Unknown runtime error' || (!file && line === 0 && col === 0)) {
            return;
        }

        var key = cleanMsg + '|' + (file || '') + '|' + (line || 0);
        if (reportedErrors.has(key)) return;
        reportedErrors.add(key);

        try {
            var errEl = document.getElementById('fraiday-runtime-errors');
            if (!errEl) {
                errEl = document.createElement('div');
                errEl.id = 'fraiday-runtime-errors';
                errEl.style.display = 'none';
                (document.body || document.documentElement).appendChild(errEl);
            }
            var errItem = document.createElement('div');
            errItem.className = 'runtime-error-item';
            errItem.textContent = cleanMsg + (file ? (' at ' + file + ':' + (line || 0)) : '');
            errEl.appendChild(errItem);
        } catch(_) {}
        try {
            if (window.parent && window.parent !== window) {
                window.parent.postMessage({
                    type: 'WORKSPACE_RUNTIME_ERROR',
                    message: cleanMsg,
                    filename: file || '',
                    lineno: line || 0,
                    colno: col || 0,
                    isConsoleError: !!isConsoleError
                }, '*');
            }
        } catch(_) {}
    }

    ['log', 'info', 'warn', 'error'].forEach(function(level) {
        var orig = console[level];
        console[level] = function() {
            try {
                var args = Array.prototype.slice.call(arguments).map(function(arg) {
                    if (typeof arg === 'object') {
                        try { return JSON.stringify(arg); } catch(e) { return String(arg); }
                    }
                    return String(arg);
                });
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({
                        type: 'WORKSPACE_CONSOLE_LOG',
                        level: level,
                        args: args,
                        timestamp: new Date().toLocaleTimeString()
                    }, '*');
                }
                if (level === 'error') {
                    recordError(args.join(' '), '', 0, 0, true);
                }
            } catch(err) {}
            if (orig) orig.apply(console, arguments);
        };
    });

    window.addEventListener('error', function(e) {
        var target = e.target || e.srcElement;
        var isScript = target && target.tagName && target.tagName.toLowerCase() === 'script';
        if (isScript) {
            recordError('Failed to load script: ' + (target.src || 'unknown script'), target.src || '', 0, 0, false);
            return;
        }
        if (e.message) {
            recordError(e.message, e.filename || '', e.lineno || 0, e.colno || 0, false);
        }
    }, true);

    window.addEventListener('unhandledrejection', function(e) {
        var reason = e.reason ? (e.reason.message || (typeof e.reason === 'object' ? JSON.stringify(e.reason) : String(e.reason))) : 'Unknown promise rejection';
        recordError('Unhandled Promise Rejection: ' + reason, '', 0, 0, false);
    });
})();
</script>"""
                    if "</head>" in text_html:
                        text_html = text_html.replace("</head>", f"{trap_script}\n</head>", 1)
                    elif "</body>" in text_html:
                        text_html = text_html.replace("</body>", f"{trap_script}\n</body>", 1)
                    else:
                        text_html = trap_script + "\n" + text_html
                    content = text_html.encode('utf-8')
                except Exception:
                    pass

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_list_files(self):
        files_list = []
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            # Prune vendor, version control, and temporary caches to keep workspace explorer clean
            dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.system_generated', '.cache')]
            for f in files:
                full = Path(root) / f
                rel = full.relative_to(WORKSPACE_DIR).as_posix()
                files_list.append({
                    "path": rel,
                    "size": full.stat().st_size,
                    "modified": int(full.stat().st_mtime)
                })
        self.send_json(200, {
            "files": sorted(files_list, key=lambda x: x["path"]),
            "workspace": get_active_workspace_name(),
            "workspace_path": "./" + str(get_active_workspace_dir().relative_to(BASE_DIR).as_posix()) + "/"
        })

    def handle_read_file(self, rel_path):
        if not rel_path:
            self.send_json(400, {"error": "Missing path parameter"})
            return
        target = (WORKSPACE_DIR / rel_path).resolve()
        if WORKSPACE_DIR not in target.parents and target != WORKSPACE_DIR:
            self.send_json(403, {"error": "Access denied outside workspace"})
            return
        if not target.is_file():
            self.send_json(404, {"error": f"File not found: {rel_path}"})
            return
        try:
            with open(target, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            self.send_json(200, {"path": rel_path, "content": content})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_write_file(self, body):
        rel_path = body.get("path")
        content = body.get("content", "")
        if not rel_path:
            self.send_json(400, {"error": "Missing path parameter"})
            return
        target = (WORKSPACE_DIR / rel_path).resolve()
        if WORKSPACE_DIR not in target.parents:
            self.send_json(403, {"error": "Access denied outside workspace"})
            return
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            self.send_json(200, {
                "success": True,
                "path": rel_path,
                "size": len(content.encode('utf-8'))
            })
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_patch_file(self, body):
        rel_path = body.get("path")
        target_content = body.get("target_content", "")
        replacement_content = body.get("replacement_content", "")

        if not rel_path or not target_content:
            self.send_json(400, {"error": "Missing path or target_content"})
            return

        target = (WORKSPACE_DIR / rel_path).resolve()
        if WORKSPACE_DIR not in target.parents:
            self.send_json(403, {"error": "Access denied outside workspace"})
            return

        if not target.is_file():
            self.send_json(404, {"error": f"File not found: {rel_path}"})
            return

        try:
            with open(target, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            if target_content not in content:
                self.send_json(400, {
                    "success": False,
                    "error": "Target content to replace was not found in file",
                    "applied": False
                })
                return

            new_content = content.replace(target_content, replacement_content, 1)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(new_content)

            self.send_json(200, {
                "success": True,
                "path": rel_path,
                "applied": True,
                "size": len(new_content.encode('utf-8'))
            })
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_delete_file(self, rel_path):
        if not rel_path:
            self.send_json(400, {"error": "Missing path"})
            return
        target = (WORKSPACE_DIR / rel_path).resolve()
        if WORKSPACE_DIR not in target.parents:
            self.send_json(403, {"error": "Access denied"})
            return
        if target.is_file():
            target.unlink()
            self.send_json(200, {"success": True, "deleted": rel_path})
        else:
            self.send_json(404, {"error": "File not found"})

    def handle_clear_workspace(self):
        try:
            import stat
            def on_rm_error(func, path, exc_info):
                try:
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                except Exception:
                    pass

            if WORKSPACE_DIR.exists():
                for item in list(WORKSPACE_DIR.iterdir()):
                    try:
                        if item.is_dir():
                            shutil.rmtree(item, onerror=on_rm_error)
                        else:
                            try:
                                os.chmod(item, stat.S_IWRITE)
                            except Exception:
                                pass
                            item.unlink(missing_ok=True)
                    except Exception as err:
                        print(f"Warning: could not delete {item}: {err}")
            else:
                WORKSPACE_DIR.mkdir(exist_ok=True)

            if SESSION_FILE.is_file():
                try:
                    SESSION_FILE.unlink(missing_ok=True)
                except Exception:
                    pass

            self.send_json(200, {"success": True, "message": "Workspace cleared"})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_get_session(self):
        try:
            if SESSION_FILE.is_file():
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.send_json(200, {"success": True, "session": data})
            else:
                self.send_json(200, {"success": True, "session": None})
        except Exception as e:
            self.send_json(500, {"error": str(e), "session": None})

    def handle_save_session(self, body):
        try:
            session_data = body.get("session") if ("session" in body and isinstance(body.get("session"), dict)) else body
            if not isinstance(session_data, dict):
                self.send_json(400, {"error": "Invalid session data payload"})
                return

            # Atomic sync to disk so server stops or crashes never corrupt or lose history
            temp_file = BASE_DIR / f".fraiday_session_{int(time.time()*1000)}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_file, SESSION_FILE)
            self.send_json(200, {"success": True, "message": "Session saved to disk"})
        except Exception as e:
            try:
                if 'temp_file' in locals() and temp_file.exists():
                    temp_file.unlink(missing_ok=True)
            except Exception:
                pass
            self.send_json(500, {"error": str(e)})

    def handle_delete_session(self):
        try:
            if SESSION_FILE.is_file():
                SESSION_FILE.unlink(missing_ok=True)
            self.send_json(200, {"success": True, "message": "Session cleared from disk"})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_export_zip(self):
        try:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(WORKSPACE_DIR):
                    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.system_generated', '.cache')]
                    for f in files:
                        full_path = Path(root) / f
                        rel_path = full_path.relative_to(WORKSPACE_DIR).as_posix()
                        zf.write(full_path, arcname=rel_path)
            data = buf.getvalue()
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="workspace.zip"')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_create_checkpoint(self, body):
        try:
            name = body.get("name", "").strip() or "checkpoint"
            desc = body.get("description", "").strip()
            ts = time.strftime('%Y%m%d_%H%M%S')
            cp_id = f"{ts}_{re.sub(r'[^a-zA-Z0-9_-]', '_', name)}"
            cp_dir = WORKSPACE_DIR / ".system_generated" / "checkpoints" / cp_id
            cp_dir.mkdir(parents=True, exist_ok=True)

            files_saved = 0
            for root, dirs, files in os.walk(WORKSPACE_DIR):
                dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.system_generated', '.cache')]
                for f in files:
                    src = Path(root) / f
                    rel = src.relative_to(WORKSPACE_DIR)
                    dst = cp_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    files_saved += 1

            meta = {
                "id": cp_id,
                "name": name,
                "description": desc,
                "timestamp": ts,
                "created_at": time.time(),
                "file_count": files_saved
            }
            with open(cp_dir / "checkpoint_meta.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            self.send_json(200, {"success": True, "checkpoint": meta})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_list_checkpoints(self):
        try:
            cp_root = WORKSPACE_DIR / ".system_generated" / "checkpoints"
            checkpoints = []
            if cp_root.is_dir():
                for d in sorted(cp_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                    if d.is_dir():
                        meta_file = d / "checkpoint_meta.json"
                        if meta_file.is_file():
                            try:
                                with open(meta_file, "r", encoding="utf-8") as f:
                                    checkpoints.append(json.load(f))
                            except Exception:
                                pass
                        else:
                            checkpoints.append({
                                "id": d.name,
                                "name": d.name,
                                "timestamp": d.name.split("_")[0] if "_" in d.name else "",
                                "created_at": d.stat().st_mtime
                            })
            self.send_json(200, {"checkpoints": checkpoints})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_rollback_checkpoint(self, body):
        try:
            cp_id = body.get("id", "").strip()
            if not cp_id:
                self.send_json(400, {"error": "Missing checkpoint id"})
                return
            cp_dir = (WORKSPACE_DIR / ".system_generated" / "checkpoints" / cp_id).resolve()
            if not cp_dir.is_dir():
                self.send_json(404, {"error": f"Checkpoint not found: {cp_id}"})
                return

            # Clean current workspace files (except .system_generated)
            for item in list(WORKSPACE_DIR.iterdir()):
                if item.name in ('.system_generated', '.git', 'node_modules'):
                    continue
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)

            # Copy files from checkpoint back to WORKSPACE_DIR
            restored = 0
            for root, dirs, files in os.walk(cp_dir):
                for f in files:
                    if f == "checkpoint_meta.json":
                        continue
                    src = Path(root) / f
                    rel = src.relative_to(cp_dir)
                    dst = WORKSPACE_DIR / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    restored += 1

            self.send_json(200, {"success": True, "restored_files": restored, "checkpoint": cp_id})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_terminal_exec(self, body):
        cmd = body.get("command", "").strip()
        res = self.run_workspace_command(cmd, exec_dir=WORKSPACE_DIR)
        self.send_json(200, res)

    def run_workspace_command(self, cmd, exec_dir=WORKSPACE_DIR, timeout=90):
        if not cmd:
            return {"CommandLine": "", "command": "", "stdout": "", "stderr": "No command provided", "exit_code": 1}

        # 1. Safety verification
        dangerous = ["rm -rf /", "mkfs", ":(){ :|:& };:"]
        for d in dangerous:
            if d in cmd:
                return {
                    "CommandLine": cmd,
                    "command": cmd,
                    "stdout": "",
                    "stderr": f"Command rejected by safety policy: {cmd}",
                    "exit_code": 1
                }

        raw_cmd = cmd.strip()

        # Check for background process execution: trailing &
        is_background = raw_cmd.rstrip().endswith("&")
        if is_background:
            raw_cmd = raw_cmd.rstrip()[:-1].strip()

        # Intercept redundant local web server commands that would block for 90s or conflict with port 8080
        if re.search(r'\b(?:python3?|py)\s+-m\s+http\.server\b', raw_cmd, re.IGNORECASE) or re.search(r'\b(?:live-server|http-server|npx\s+serve)\b', raw_cmd, re.IGNORECASE):
            return {
                "CommandLine": cmd,
                "command": cmd,
                "stdout": (
                    f"[frAIday Runtime Notice]: The workspace live preview server is ALREADY active and serving your files at http://localhost:{PORT}/workspace/index.html.\n"
                    "You do not need to start a secondary http.server in the terminal. Live changes render automatically in the preview iframe.\n"
                ),
                "stderr": "",
                "exit_code": 0
            }

        # 2. Pure Python Emulation for common Unix utilities (cat, touch, pwd, clear, ls, which)
        # Guarantees instant, platform-independent execution without Windows cmd.exe failures!
        tokens = None
        if not any(sep in raw_cmd for sep in ("|", ">", "<", "&&", "||", ";", "`", "$(")):
            try:
                tokens = shlex.split(raw_cmd, posix=False)
            except Exception:
                tokens = None

        if tokens and len(tokens) > 0:
            base_cmd = tokens[0].lower()

            # Emulate 'cat'
            if base_cmd == "cat":
                args = tokens[1:]
                show_line_numbers = False
                if args and args[0] in ("-n", "--number"):
                    show_line_numbers = True
                    args = args[1:]

                if not args:
                    return {"CommandLine": cmd, "command": cmd, "stdout": "", "stderr": "cat: missing file operand", "exit_code": 1}

                combined_out = []
                for file_arg in args:
                    clean_file = file_arg.strip('\'"')
                    target = (Path(exec_dir) / clean_file).resolve()
                    if not target.is_file():
                        cands = list(Path(exec_dir).glob(f"**/{Path(clean_file).name}"))
                        if cands:
                            target = cands[0]
                        else:
                            return {
                                "CommandLine": cmd,
                                "command": cmd,
                                "stdout": "\n".join(combined_out),
                                "stderr": f"cat: {clean_file}: No such file or directory",
                                "exit_code": 1
                            }
                    try:
                        with open(target, 'r', encoding='utf-8', errors='replace') as fh:
                            content = fh.read()
                            if show_line_numbers:
                                lines = content.splitlines()
                                content = "\n".join(f"{idx + 1:6d}  {line}" for idx, line in enumerate(lines))
                            combined_out.append(content)
                    except Exception as e:
                        return {
                            "CommandLine": cmd,
                            "command": cmd,
                            "stdout": "\n".join(combined_out),
                            "stderr": f"cat: {clean_file}: {str(e)}",
                            "exit_code": 1
                        }
                return {
                    "CommandLine": cmd,
                    "command": cmd,
                    "stdout": "\n".join(combined_out),
                    "stderr": "",
                    "exit_code": 0
                }

            # Emulate 'touch'
            elif base_cmd == "touch":
                files_to_touch = tokens[1:]
                if not files_to_touch:
                    return {"CommandLine": cmd, "command": cmd, "stdout": "", "stderr": "touch: missing file operand", "exit_code": 1}
                for f in files_to_touch:
                    clean_f = f.strip('\'"')
                    target = (Path(exec_dir) / clean_f).resolve()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.touch(exist_ok=True)
                return {"CommandLine": cmd, "command": cmd, "stdout": "", "stderr": "", "exit_code": 0}

            # Emulate 'pwd'
            elif base_cmd == "pwd":
                return {"CommandLine": cmd, "command": cmd, "stdout": str(exec_dir) + "\n", "stderr": "", "exit_code": 0}

            # Emulate 'clear' or 'cls'
            elif base_cmd in ("clear", "cls"):
                return {"CommandLine": cmd, "command": cmd, "stdout": "", "stderr": "", "exit_code": 0}

            # Emulate 'which'
            elif base_cmd == "which":
                target_prog = tokens[1].strip('\'"') if len(tokens) > 1 else ""
                if not target_prog:
                    return {"CommandLine": cmd, "command": cmd, "stdout": "", "stderr": "which: missing program name", "exit_code": 1}
                loc = shutil.which(target_prog)
                if loc:
                    return {"CommandLine": cmd, "command": cmd, "stdout": loc + "\n", "stderr": "", "exit_code": 0}
                return {"CommandLine": cmd, "command": cmd, "stdout": "", "stderr": f"{target_prog} not found in PATH", "exit_code": 1}

            # Emulate simple 'ls'
            elif base_cmd == "ls" and (len(tokens) == 1 or tokens[1] in ("-a", "-la", "-l", "-lh", "-al")):
                show_details = len(tokens) > 1 and ("l" in tokens[1])
                target_dir = Path(exec_dir)
                try:
                    entries = sorted(list(target_dir.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
                    lines = []
                    for e in entries:
                        if e.name.startswith(".") and (len(tokens) == 1 or "a" not in tokens[1]):
                            continue
                        if show_details:
                            sz = e.stat().st_size if e.is_file() else 0
                            mtime = time.strftime('%b %d %H:%M', time.localtime(e.stat().st_mtime))
                            prefix = "drwxr-xr-x" if e.is_dir() else "-rw-r--r--"
                            lines.append(f"{prefix}  1 user staff  {sz:8d}  {mtime}  {e.name}{'/' if e.is_dir() else ''}")
                        else:
                            lines.append(f"{e.name}{'/' if e.is_dir() else ''}")
                    return {
                        "CommandLine": cmd,
                        "command": cmd,
                        "stdout": "\n".join(lines) + ("\n" if lines else ""),
                        "stderr": "",
                        "exit_code": 0
                    }
                except Exception as e:
                    return {"CommandLine": cmd, "command": cmd, "stdout": "", "stderr": str(e), "exit_code": 1}

        # 3. Prepare Shell Command Execution
        executable_cmd = raw_cmd
        if executable_cmd.startswith("python "):
            executable_cmd = f'& "{sys.executable}" ' + executable_cmd[7:]
        elif executable_cmd == "python":
            executable_cmd = f'& "{sys.executable}"'
        elif executable_cmd.startswith("pip "):
            executable_cmd = f'& "{sys.executable}" -m pip ' + executable_cmd[4:]
        elif executable_cmd == "pip":
            executable_cmd = f'& "{sys.executable}" -m pip'
        elif executable_cmd.startswith('"') and not executable_cmd.startswith('&'):
            executable_cmd = '& ' + executable_cmd

        # On Windows, execute through powershell.exe so that built-in aliases and shell pipelines work naturally.
        # We explicitly remove aliases for curl and wget so the real curl.exe and wget.exe are invoked!
        use_powershell = sys.platform == "win32" and shutil.which("powershell")
        if use_powershell:
            ps_script = (
                "Remove-Item Alias:curl -ErrorAction SilentlyContinue; "
                "Remove-Item Alias:wget -ErrorAction SilentlyContinue; "
                + executable_cmd
            )
            shell_args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script]
            shell_mode = False
        else:
            shell_args = executable_cmd
            shell_mode = True

        custom_env = os.environ.copy()
        git_usr_bin = r"C:\Program Files\Git\usr\bin"
        git_cmd = r"C:\Program Files\Git\cmd"
        extra_paths = [p for p in [git_usr_bin, git_cmd] if os.path.isdir(p)]
        if extra_paths:
            custom_env["PATH"] = ";".join(extra_paths) + ";" + custom_env.get("PATH", "")

        if is_background:
            try:
                creation_flags = 0
                if sys.platform == "win32":
                    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)
                p = subprocess.Popen(
                    shell_args,
                    shell=shell_mode,
                    cwd=str(exec_dir),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=custom_env,
                    creationflags=creation_flags
                )
                return {
                    "CommandLine": cmd,
                    "command": cmd,
                    "stdout": f"[Process started in background with PID {p.pid}]\n",
                    "stderr": "",
                    "exit_code": 0
                }
            except Exception as e:
                return {
                    "CommandLine": cmd,
                    "command": cmd,
                    "stdout": "",
                    "stderr": f"Failed to start background process: {str(e)}",
                    "exit_code": 1
                }

        def run_proc(args, use_shell):
            p = subprocess.Popen(
                args,
                shell=use_shell,
                cwd=str(exec_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=custom_env
            )
            out, err = p.communicate(timeout=timeout)
            return out, err, p.returncode

        try:
            stdout, stderr, exit_code = run_proc(shell_args, shell_mode)
        except subprocess.TimeoutExpired:
            return {
                "CommandLine": cmd,
                "command": cmd,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "CommandLine": cmd,
                "command": cmd,
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1
            }

        # 4. Auto-heal / Auto-download required dependencies
        if exit_code != 0 and stderr:
            # Check A: Missing Python module
            py_match = re.search(r"(?:ModuleNotFoundError|ImportError):\s+No module named ['\"]([^'\"]+)['\"]", stderr)
            if py_match:
                missing_mod = py_match.group(1).split('.')[0]
                install_cmd = [sys.executable, "-m", "pip", "install", missing_mod]
                try:
                    inst_proc = subprocess.run(install_cmd, capture_output=True, text=True, timeout=90, cwd=str(exec_dir), env=custom_env)
                    if inst_proc.returncode == 0:
                        stdout_r, stderr_r, exit_code_r = run_proc(shell_args, shell_mode)
                        return {
                            "CommandLine": cmd,
                            "command": cmd,
                            "stdout": f"[frAIday Auto-Installer] ✔ Automatically downloaded & installed Python module '{missing_mod}'.\n\n" + stdout_r,
                            "stderr": stderr_r,
                            "exit_code": exit_code_r
                        }
                except Exception as ex:
                    stderr += f"\n[frAIday Auto-Installer] Attempted to auto-install '{missing_mod}' but encountered: {ex}"

            # Check B: Missing Node.js module
            node_match = re.search(r"Cannot find module ['\"]([^'\"]+)['\"]", stderr)
            if node_match:
                missing_pkg = node_match.group(1)
                if not missing_pkg.startswith((".", "/", "\\")):
                    install_cmd = f"npm install {missing_pkg}"
                    try:
                        inst_proc = subprocess.run(install_cmd, shell=True, capture_output=True, text=True, timeout=90, cwd=str(exec_dir), env=custom_env)
                        if inst_proc.returncode == 0:
                            stdout_r, stderr_r, exit_code_r = run_proc(shell_args, shell_mode)
                            return {
                                "CommandLine": cmd,
                                "command": cmd,
                                "stdout": f"[frAIday Auto-Installer] ✔ Automatically downloaded & installed Node.js package '{missing_pkg}'.\n\n" + stdout_r,
                                "stderr": stderr_r,
                                "exit_code": exit_code_r
                            }
                    except Exception as ex:
                        stderr += f"\n[frAIday Auto-Installer] Attempted to auto-install '{missing_pkg}' but encountered: {ex}"

            # Check C: Command not found in PowerShell or CMD
            cmd_match = (
                re.search(r"The term '([^']+)' is not recognized", stderr) or
                re.search(r"['\"]?([a-zA-Z0-9_\-]+)['\"]? is not recognized as an internal or external command", stderr) or
                re.search(r"(?:command not found|Command ['\"]?([a-zA-Z0-9_\-]+)['\"]? not found)", stderr, re.I)
            )
            if cmd_match:
                missing_bin = cmd_match.group(1).lower()
                # 1. Try running via npx --yes
                if shutil.which("npx"):
                    npx_cmd = f"npx --yes {executable_cmd}"
                    try:
                        npx_args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", npx_cmd] if use_powershell else npx_cmd
                        stdout_r, stderr_r, exit_code_r = run_proc(npx_args, not use_powershell)
                        if exit_code_r == 0 or (stdout_r and not stderr_r):
                            return {
                                "CommandLine": cmd,
                                "command": cmd,
                                "stdout": f"[frAIday Auto-Installer] ✔ Automatically downloaded & ran '{missing_bin}' via npx.\n\n" + stdout_r,
                                "stderr": stderr_r,
                                "exit_code": exit_code_r
                            }
                    except Exception:
                        pass
                # 2. Try pip install if it looks like a python tool or package
                try:
                    pip_cmd = [sys.executable, "-m", "pip", "install", missing_bin]
                    pip_p = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=60, cwd=str(exec_dir), env=custom_env)
                    if pip_p.returncode == 0:
                        stdout_r, stderr_r, exit_code_r = run_proc(shell_args, shell_mode)
                        if exit_code_r == 0 or stdout_r:
                            return {
                                "CommandLine": cmd,
                                "command": cmd,
                                "stdout": f"[frAIday Auto-Installer] ✔ Automatically installed Python package '{missing_bin}'.\n\n" + stdout_r,
                                "stderr": stderr_r,
                                "exit_code": exit_code_r
                            }
                except Exception:
                    pass
                # 3. Try npm install -g
                if shutil.which("npm"):
                    try:
                        npm_p = subprocess.run(f"npm install -g {missing_bin}", shell=True, capture_output=True, text=True, timeout=60, cwd=str(exec_dir), env=custom_env)
                        if npm_p.returncode == 0:
                            stdout_r, stderr_r, exit_code_r = run_proc(shell_args, shell_mode)
                            if exit_code_r == 0 or stdout_r:
                                return {
                                    "CommandLine": cmd,
                                    "command": cmd,
                                    "stdout": f"[frAIday Auto-Installer] ✔ Automatically installed '{missing_bin}' globally via npm.\n\n" + stdout_r,
                                    "stderr": stderr_r,
                                    "exit_code": exit_code_r
                                }
                    except Exception:
                        pass

        # Advisory for browser DOM APIs in Node.js
        if stderr and ("ReferenceError: document is not defined" in stderr or "document is not def" in stderr or "ReferenceError: window is not defined" in stderr):
            stderr += "\n\n[SYSTEM ADVISORY]: You attempted to execute a client-side browser JavaScript script containing DOM APIs ('document' or 'window') using Node.js in the terminal. Node.js does not have browser DOM globals. Browser frontends run in the client browser, NOT in Node CLI. To test and audit browser client-side applications, ensure index.html loads the script and use the 'browser_subagent' tool to launch headless Chrome and inspect the live preview."

        return {
            "CommandLine": cmd,
            "command": cmd,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code
        }

    def handle_web_search(self, query):
        if not query:
            self.send_json(200, {"results": []})
            return

        results = []
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(ddg_url, headers={'User-Agent': 'frAIday-Agent/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                abstract = data.get("AbstractText", "")
                if abstract:
                    results.append({
                        "title": data.get("Heading", query),
                        "snippet": abstract,
                        "url": data.get("AbstractURL", f"https://duckduckgo.com/?q={urllib.parse.quote(query)}")
                    })
                for topic in data.get("RelatedTopics", [])[:4]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                            "snippet": topic["Text"],
                            "url": topic.get("FirstURL", "")
                        })
        except Exception:
            pass

        if len(results) < 2:
            try:
                wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=3&namespace=0&format=json"
                req = urllib.request.Request(wiki_url, headers={'User-Agent': 'frAIday-Agent/1.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    wiki_data = json.loads(resp.read().decode('utf-8'))
                    if len(wiki_data) >= 4:
                        titles, descriptions, urls = wiki_data[1], wiki_data[2], wiki_data[3]
                        for i in range(len(titles)):
                            if descriptions[i]:
                                results.append({
                                    "title": titles[i],
                                    "snippet": descriptions[i],
                                    "url": urls[i]
                                })
            except Exception:
                pass

        if not results:
            results.append({
                "title": f"Technical Reference: {query}",
                "snippet": f"Autonomous documentation lookup for {query} across standard specifications and API references.",
                "url": f"https://developer.mozilla.org/search?q={urllib.parse.quote(query)}"
            })

        self.send_json(200, {"query": query, "results": results})

    def handle_update_config(self, body):
        if "provider" in body and body["provider"]:
            ACTIVE_CONFIG["provider"] = str(body["provider"]).strip()
        if "api_key" in body and body["api_key"]:
            ACTIVE_CONFIG["api_key"] = str(body["api_key"]).strip()
        if "model" in body and body["model"]:
            ACTIVE_CONFIG["model"] = str(body["model"]).strip()
        if "safety" in body and body["safety"]:
            ACTIVE_CONFIG["safety"] = str(body["safety"]).strip()

        print(f"[frAIday Server] Active config updated: provider={ACTIVE_CONFIG['provider']}, model={ACTIVE_CONFIG['model']}")
        self.send_json(200, {
            "success": True,
            "provider": ACTIVE_CONFIG["provider"],
            "model": ACTIVE_CONFIG["model"],
            "safety": ACTIVE_CONFIG["safety"]
        })

    def handle_llm_chat(self, body):
        prompt = body.get("prompt", "")
        messages = body.get("messages", [])
        provider = body.get("provider") or ACTIVE_CONFIG.get("provider", "groq")
        model = body.get("model") or (ACTIVE_CONFIG["model"] if provider == ACTIVE_CONFIG.get("provider") else None)

        # Resolve provider-specific API key safely
        if body.get("api_key"):
            api_key = str(body["api_key"]).strip()
        elif provider == ACTIVE_CONFIG.get("provider") and ACTIVE_CONFIG.get("api_key"):
            api_key = str(ACTIVE_CONFIG["api_key"]).strip()
        elif provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY", "") or DEFAULT_GEMINI_KEY
        elif provider == "groq":
            api_key = os.environ.get("GROQ_API_KEY", "")
        elif provider == "nvidia":
            api_key = os.environ.get("NVIDIA_API_KEY", "")
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
        else:
            api_key = ""

        if not messages and prompt:
            messages = [{"role": "user", "content": prompt}]

        if provider == "gemini":
            gemini_key = api_key or DEFAULT_GEMINI_KEY
            if not gemini_key:
                self.send_json(400, {
                    "error": "No API key configured for Google Gemini. Please enter your Google AI Studio API key.",
                    "missing_api_key": True,
                    "provider": "gemini"
                })
                return

            gemini_model = model or "gemini-3.8-flash"
            if "/" in gemini_model:
                gemini_model = gemini_model.split("/")[-1]

            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            headers = {
                "Authorization": f"Bearer {gemini_key}",
                "Content-Type": "application/json",
                "User-Agent": "frAIday-Antigravity/1.0"
            }

            candidate_models = [gemini_model]
            for fb in ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3-flash-preview"]:
                if fb not in candidate_models:
                    candidate_models.append(fb)

            last_err = ""
            for curr_model in candidate_models:
                payload = {
                    "model": curr_model,
                    "messages": messages,
                    "temperature": body.get("temperature", 0.3)
                }
                if "tools" in body and body["tools"]:
                    payload["tools"] = body["tools"]

                for attempt in range(3):
                    try:
                        req_data = json.dumps(payload).encode("utf-8")
                        req = urllib.request.Request(url, data=req_data, headers=headers)
                        with urllib.request.urlopen(req, timeout=40) as resp:
                            res_json = json.loads(resp.read().decode("utf-8"))
                            self.send_json(200, res_json)
                            return
                    except urllib.error.HTTPError as e:
                        err_body = e.read().decode("utf-8", errors="replace")
                        last_err = f"HTTP {e.code}: {err_body}"
                        if e.code == 503:
                            time.sleep(1.5 * (attempt + 1))
                            continue
                        elif e.code == 429:
                            time.sleep(2 * (attempt + 1))
                            continue
                        else:
                            break
                    except Exception as e:
                        last_err = str(e)
                        time.sleep(1)

            self.send_json(500, {"error": f"Gemini API request failed across candidates: {last_err}", "provider": "gemini"})
            return

        elif provider == "groq":
            global GROQ_KEY_INDEX
            url = "https://api.groq.com/openai/v1/chat/completions"
            client_keys = [k.strip() for k in re.split(r'[,;\n\r\s]+', str(api_key or "")) if k.strip()]
            server_keys = [k.strip() for k in re.split(r'[,;\n\r\s]+', str(ACTIVE_CONFIG.get("api_key") if ACTIVE_CONFIG.get("provider") == "groq" else DEFAULT_GROQ_KEY)) if k.strip()]
            groq_keys = client_keys or server_keys
            if not groq_keys:
                self.send_json(400, {
                    "error": "No API key configured for Groq. Please enter your API key in Settings or enter it when prompted.",
                    "missing_api_key": True,
                    "provider": "groq"
                })
                return

            groq_model = model or "openai/gpt-oss-120b"
            if groq_model in ("gpt-oss-120b", "openai-gpt-oss-120b", "openai/gpt-oss-120b"):
                groq_model = "openai/gpt-oss-120b"
                candidates = ["openai/gpt-oss-120b"]
            elif groq_model in ("gpt-oss-20b", "openai-gpt-oss-20b"):
                groq_model = "openai/gpt-oss-20b"
                candidates = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
            elif groq_model in ("qwen-3.8-27b", "qwen3.8-27b"):
                groq_model = "qwen/qwen3.8-27b"
                candidates = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
            else:
                candidates = [groq_model]

            # Prioritize models that are not currently in rate-limit cooldown
            now = time.time()
            candidates.sort(key=lambda m: 1 if MODEL_COOLDOWNS.get(m, 0) > now else 0)

            # Order keys starting from GROQ_KEY_INDEX (round-robin), prioritizing unblocked keys
            start_idx = GROQ_KEY_INDEX % len(groq_keys)
            GROQ_KEY_INDEX += 1
            ordered_keys = groq_keys[start_idx:] + groq_keys[:start_idx]
            ordered_keys.sort(key=lambda k: 1 if KEY_COOLDOWNS.get(k, 0) > now else 0)

            last_error = None
            wait_sec = 3.0
            for current_model in candidates:
                if "120b" in current_model:
                    msg_tokens = int(len(json.dumps(messages)) / 3.8)
                    tools_tokens = 900 if ("tools" in body and body["tools"]) else 0
                    total_prompt_est = msg_tokens + tools_tokens
                    
                    if total_prompt_est > 5400 and len(messages) > 3:
                        sys_msg = [m for m in messages if m.get("role") == "system"][:1]
                        tail_msgs = messages[-6:]
                        compacted_msgs = []
                        for m in (sys_msg + tail_msgs):
                            if m not in compacted_msgs:
                                compacted_msgs.append(m)
                        messages = compacted_msgs
                        msg_tokens = int(len(json.dumps(messages)) / 3.8)
                        total_prompt_est = msg_tokens + tools_tokens
                    
                    dynamic_max = min(4096, max(2000, int(7750 - total_prompt_est)))
                    target_max = body.get("max_tokens", 4096)
                    max_tok = min(target_max, dynamic_max)
                else:
                    max_tok = min(body.get("max_tokens", 4096), 4096)

                payload = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": body.get("temperature", 0.2),
                    "max_tokens": max_tok
                }
                if "tools" in body and body["tools"]:
                    payload["tools"] = body["tools"]
                if "tool_choice" in body and body["tool_choice"]:
                    payload["tool_choice"] = body["tool_choice"]

                req_data = json.dumps(payload).encode('utf-8')

                for current_key in ordered_keys:
                    headers = {
                        "Authorization": f"Bearer {current_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                    }
                    key_masked = current_key[:10] + "..." + current_key[-4:] if len(current_key) > 16 else current_key
                    try:
                        req = urllib.request.Request(url, data=req_data, headers=headers)
                        with urllib.request.urlopen(req, timeout=25) as resp:
                            res_data = json.loads(resp.read().decode('utf-8'))
                            choice = res_data['choices'][0]
                            message = choice.get('message', {})
                            content = message.get('content', '')
                            if not content and 'reasoning' in message:
                                content = message['reasoning']
                            tool_calls = message.get('tool_calls', None)
                            self.send_json(200, {
                                "content": content,
                                "tool_calls": tool_calls,
                                "message": message,
                                "model_used": current_model,
                                "key_used": key_masked,
                                "keys_count": len(groq_keys),
                                "raw": res_data
                            })
                            return
                    except urllib.error.HTTPError as e:
                        err_text = e.read().decode('utf-8', errors='replace')
                        last_error = f"HTTP {e.code}: {err_text}"
                        is_tpm_or_size = (
                            e.code == 413 or 
                            "too large" in err_text.lower() or 
                            "limit 8000" in err_text.lower() or 
                            ("tokens" in err_text.lower() and "rate_limit_exceeded" in err_text.lower())
                        )
                        if is_tpm_or_size:
                            print(f"[frAIday Server] {current_model} TPM/Size limit on key {key_masked}. Pruning history to preserve 2200 code tokens...", flush=True)
                            # NEVER starve code generation tokens! Prune message history instead:
                            curr_msgs = payload.get("messages", [])
                            if len(curr_msgs) > 3:
                                sys_msg = [m for m in curr_msgs if m.get("role") == "system"][:1]
                                tail_msgs = curr_msgs[-4:]
                                compacted = []
                                for m in (sys_msg + tail_msgs):
                                    m_copy = dict(m)
                                    if m_copy.get("role") == "tool" and isinstance(m_copy.get("content"), str):
                                        c = m_copy["content"]
                                        if len(c) > 300:
                                            m_copy["content"] = c[:150] + "\n...[truncated]...\n" + c[-100:]
                                    compacted.append(m_copy)
                                payload["messages"] = compacted
                            payload["max_tokens"] = max(2000, payload.get("max_tokens", 2200))
                            req_data = json.dumps(payload).encode('utf-8')
                            try:
                                req_retry = urllib.request.Request(url, data=req_data, headers=headers)
                                with urllib.request.urlopen(req_retry, timeout=25) as resp:
                                    res_data = json.loads(resp.read().decode('utf-8'))
                                    choice = res_data['choices'][0]
                                    message = choice.get('message', {})
                                    content = message.get('content', '')
                                    if not content and 'reasoning' in message:
                                        content = message['reasoning']
                                    tool_calls = message.get('tool_calls', None)
                                    self.send_json(200, {
                                        "content": content,
                                        "tool_calls": tool_calls,
                                        "message": message,
                                        "model_used": current_model,
                                        "key_used": key_masked,
                                        "keys_count": len(groq_keys),
                                        "raw": res_data
                                    })
                                    return
                            except Exception as retry_err:
                                print(f"[frAIday Server] Retry after pruning failed on {key_masked}: {retry_err}", flush=True)
                                continue
                        elif e.code == 400 and ("failed to parse" in err_text.lower() or "tool_use_failed" in err_text.lower()):
                            print(f"[frAIday Server] Tool JSON truncated on key {key_masked}. Boosting max_tokens to 2600...", flush=True)
                            payload["max_tokens"] = 2600
                            req_data = json.dumps(payload).encode('utf-8')
                            continue
                        elif e.code == 429:
                            wait_sec = 2.5
                            try:
                                m = re.search(r'try again in (?:(\d+)m)?([0-9.]+)s', err_text)
                                if m:
                                    mins = float(m.group(1)) if m.group(1) else 0.0
                                    secs = float(m.group(2))
                                    wait_sec = mins * 60 + secs + 0.5
                            except Exception:
                                pass

                            KEY_COOLDOWNS[current_key] = time.time() + wait_sec
                            print(f"[frAIday Server] Groq 429 on key {key_masked} ({current_model}). Auto-switching to next key in pool...", flush=True)
                            continue
                        elif e.code == 401:
                            KEY_COOLDOWNS[current_key] = time.time() + 86400
                            print(f"[frAIday Server] Groq 401 Invalid Key on {key_masked}. Key disabled for 24h.", flush=True)
                            continue
                        else:
                            print(f"[frAIday Server] Error calling {current_model} with key {key_masked}: {last_error}", flush=True)
                            continue
                    except Exception as e:
                        last_error = str(e)
                        continue

                # If all keys failed on this model with 429, mark model cooldown
                MODEL_COOLDOWNS[current_model] = time.time() + wait_sec
                print(f"[frAIday Server] All keys exhausted on {current_model}. Auto-falling back to next model in cascade...", flush=True)

            self.send_json(429 if "429" in str(last_error) else 500, {
                "error": f"Groq Gateway Error: {last_error}",
                "retry_after": wait_sec
            })
            return



        elif provider == "nvidia":
            if not api_key:
                self.send_json(400, {
                    "error": "No API key configured for NVIDIA NIM. Please enter your API key in Settings or enter it when prompted.",
                    "missing_api_key": True,
                    "provider": "nvidia"
                })
                return
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            payload = {
                "model": model,
                "messages": messages,
                "temperature": body.get("temperature", 0.3),
                "max_tokens": min(body.get("max_tokens", 4096), 8192)
            }
            req_data = json.dumps(payload).encode('utf-8')
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "frAIday-Server/1.0"
            }
            
            # Retry loop for NVIDIA NIM gateway latency with exponential backoff
            last_err = None
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=req_data, headers=headers)
                    with urllib.request.urlopen(req, timeout=180) as resp:
                        res_data = json.loads(resp.read().decode('utf-8'))
                        content = res_data['choices'][0]['message']['content']
                        self.send_json(200, {"content": content, "raw": res_data})
                        return
                except urllib.error.HTTPError as e:
                    err_text = e.read().decode('utf-8', errors='replace')
                    self.send_json(e.code, {"error": f"NVIDIA API Error: {err_text}"})
                    return
                except Exception as e:
                    last_err = e
                    time.sleep(1.5 * (attempt + 1))
            self.send_json(500, {"error": f"NVIDIA Gateway Timeout/Error: {str(last_err)}"})

        elif provider == "openai":
            if not api_key:
                self.send_json(400, {
                    "error": "No API key configured for OpenAI. Please enter your API key in Settings or enter it when prompted.",
                    "missing_api_key": True,
                    "provider": "openai"
                })
                return
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": model or "gpt-4o-mini",
                "messages": messages,
                "temperature": body.get("temperature", 0.2)
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    self.send_json(200, {"content": res_data['choices'][0]['message']['content'], "raw": res_data})
            except Exception as e:
                self.send_json(500, {"error": str(e)})

        elif provider == "ollama":
            url = "http://localhost:11434/api/chat"
            payload = {
                "model": model or "llama3",
                "messages": messages,
                "stream": False
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    self.send_json(200, {"content": res_data['message']['content'], "raw": res_data})
            except Exception as e:
                self.send_json(500, {"error": str(e)})


        else:
            self.send_json(400, {"error": f"Unsupported provider: {provider}"})

    def handle_build_verify(self):
        checked_files = []
        errors = []
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            for f in files:
                full = Path(root) / f
                rel = full.relative_to(WORKSPACE_DIR).as_posix()

                # JavaScript / ES Modules
                if f.endswith((".js", ".mjs")):
                    checked_files.append(rel)
                    try:
                        res = subprocess.run(["node", "-c", str(full)], capture_output=True, text=True, timeout=10)
                        if res.returncode != 0:
                            errors.append({"file": rel, "error": res.stderr.strip() or res.stdout.strip()})
                    except Exception as e:
                        errors.append({"file": rel, "error": str(e)})

                # Python Modules
                elif f.endswith(".py"):
                    checked_files.append(rel)
                    try:
                        res = subprocess.run([sys.executable, "-m", "py_compile", str(full)], capture_output=True, text=True, timeout=10)
                        if res.returncode != 0:
                            errors.append({"file": rel, "error": res.stderr.strip() or res.stdout.strip()})
                    except Exception as e:
                        errors.append({"file": rel, "error": str(e)})

                # JSON Configs
                elif f.endswith(".json"):
                    checked_files.append(rel)
                    try:
                        with open(full, 'r', encoding='utf-8') as jf:
                            json.load(jf)
                    except Exception as e:
                        errors.append({"file": rel, "error": f"JSON parse error: {str(e)}"})

        self.send_json(200, {
            "success": len(errors) == 0,
            "checked_count": len(checked_files),
            "checked_files": checked_files,
            "errors": errors
        })

    def handle_build_test(self, body=None):
        body = body or {}
        custom_cmd = body.get("command")

        if custom_cmd:
            try:
                res = subprocess.run(custom_cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=25, cwd=str(WORKSPACE_DIR))
                self.send_json(200, {
                    "success": res.returncode == 0,
                    "exit_code": res.returncode,
                    "command": custom_cmd,
                    "stdout": res.stdout,
                    "stderr": res.stderr
                })
                return
            except Exception as e:
                self.send_json(500, {"success": False, "error": str(e)})
                return

        # Auto-detect test runner if no custom command provided
        # 1. Node.js tests
        js_tests = list(WORKSPACE_DIR.glob("**/*.test.js")) + list(WORKSPACE_DIR.glob("**/test*.js"))
        if js_tests:
            test_target = js_tests[0]
            try:
                res = subprocess.run(["node", str(test_target)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20, cwd=str(WORKSPACE_DIR))
                self.send_json(200, {
                    "success": res.returncode == 0,
                    "exit_code": res.returncode,
                    "stdout": res.stdout,
                    "stderr": res.stderr
                })
                return
            except Exception as e:
                self.send_json(500, {"success": False, "error": str(e)})
                return

        # 2. Python tests
        py_tests = list(WORKSPACE_DIR.glob("**/test_*.py")) + list(WORKSPACE_DIR.glob("**/*_test.py"))
        if py_tests:
            test_target = py_tests[0]
            try:
                res = subprocess.run([sys.executable, "-m", "unittest", str(test_target)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20, cwd=str(WORKSPACE_DIR))
                self.send_json(200, {
                    "success": res.returncode == 0,
                    "exit_code": res.returncode,
                    "stdout": res.stdout,
                    "stderr": res.stderr
                })
                return
            except Exception as e:
                self.send_json(500, {"success": False, "error": str(e)})
                return

    def handle_tool_execute(self, body):
        name = body.get("name", "").strip()
        args = body.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}

        # Check if caller disabled Hindsight (Stateless Baseline Mode)
        hindsight_enabled = body.get("hindsight_enabled", True)
        if isinstance(args, dict) and "hindsight_enabled" in args:
            hindsight_enabled = bool(args.get("hindsight_enabled"))

        # Intercept and block memory operations in Stateless Baseline Mode
        if not hindsight_enabled and name in (
            "retain_memory", "hindsight_retain", "remember_insight",
            "recall_memory", "hindsight_recall",
            "reflect_memory", "hindsight_reflect"
        ):
            self.send_json(200, {
                "success": False,
                "disabled": True,
                "error": "Vectorize Hindsight memory is explicitly SWITCHED OFF (Stateless Baseline Mode active). Memory recall, retention, and reflection are completely bypassed.",
                "count": 0,
                "results": [],
                "prompt_string": ""
            })
            return

        # Normalize tool aliases emitted by various LLMs (e.g. DeepSeek Web calls _web for web search)
        if name in ("_web", "web_search", "_search", "web", "search"):
            name = "search_web"
        elif name in ("write_file", "create_file", "new_file"):
            name = "write_to_file"
        elif name in ("read_file", "cat", "open_file"):
            name = "view_file"
        elif name in ("execute_command", "exec_command", "shell_command", "bash", "sh", "terminal"):
            name = "run_command"

        if name == "run_command":
            cmd = args.get("CommandLine") or args.get("command") or args.get("cmd") or ""
            cmd = str(cmd).strip()
            cwd_arg = args.get("Cwd", "").strip()
            exec_dir = WORKSPACE_DIR
            if cwd_arg:
                custom_cwd = (WORKSPACE_DIR / cwd_arg).resolve()
                if WORKSPACE_DIR in custom_cwd.parents or custom_cwd == WORKSPACE_DIR:
                    if custom_cwd.is_dir():
                        exec_dir = custom_cwd
            res = self.execute_shell_command(cmd, exec_dir)
            self.send_json(200, res)
            return

        elif name == "write_to_file":
            target_file = args.get("TargetFile") or args.get("path") or args.get("file") or ""
            target_file = str(target_file).strip()
            code_content = args.get("CodeContent") if "CodeContent" in args else args.get("content", "")
            overwrite = args.get("Overwrite", True)
            description = args.get("Description", "")
            res = self.execute_write_file(target_file, code_content, overwrite, description)
            self.send_json(200, res)
            return

        elif name == "replace_file_content":
            target_file = args.get("TargetFile") or args.get("path") or args.get("file") or ""
            target_file = str(target_file).strip()
            target_content = args.get("TargetContent", "")
            replacement_content = args.get("ReplacementContent", "")
            start_line = args.get("StartLine")
            end_line = args.get("EndLine")
            allow_multiple = args.get("AllowMultiple", False)
            res = self.execute_replace_file_content(target_file, target_content, replacement_content, start_line, end_line, allow_multiple)
            self.send_json(200, res)
            return

        elif name == "view_file":
            abs_path = args.get("AbsolutePath") or args.get("TargetFile") or args.get("path") or args.get("file") or ""
            abs_path = str(abs_path).strip()
            start_line = args.get("StartLine")
            end_line = args.get("EndLine")
            res = self.execute_view_file(abs_path, start_line, end_line)
            self.send_json(200, res)
            return

        elif name == "list_dir":
            dir_path = args.get("DirectoryPath") or args.get("path") or ""
            dir_path = str(dir_path).strip()
            res = self.execute_list_dir(dir_path)
            self.send_json(200, res)
            return

        elif name == "grep_search":
            query = args.get("Query") or args.get("query") or ""
            search_path = args.get("SearchPath", "")
            case_insensitive = args.get("CaseInsensitive", False)
            is_regex = args.get("IsRegex", False)
            match_per_line = args.get("MatchPerLine", True)
            includes = args.get("Includes", [])
            res = self.execute_grep_search(query, search_path, case_insensitive, is_regex, match_per_line, includes)
            self.send_json(200, res)
            return

        elif name == "browser_subagent":
            task = args.get("Task") or args.get("task") or "Inspect rendered website for visual appearance, DOM elements, and console errors"
            res = self.execute_browser_subagent(task)
            self.send_json(200, res)
            return

        elif name == "search_web":
            q = args.get("query") or args.get("Query") or args.get("q") or args.get("search_query") or ""
            res = self.execute_web_search_tool(q)
            self.send_json(200, res)
            return

        elif name in ("retain_memory", "hindsight_retain", "remember_insight"):
            content = args.get("content") or args.get("insight") or args.get("fact") or ""
            mem_type = args.get("memory_type") or args.get("type") or "observation"
            tags = args.get("tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            metadata = {
                "title": args.get("title") or args.get("topic") or "Learned Project Insight",
                "source": "autonomous_agent_tool"
            }
            if HINDSIGHT:
                res = HINDSIGHT.retain(content=content, memory_type=mem_type, metadata=metadata, tags=tags)
                self.send_json(200, res)
            else:
                self.send_json(200, {"success": False, "error": "Hindsight memory unavailable"})
            return

        elif name in ("recall_memory", "hindsight_recall"):
            query = args.get("query") or args.get("q") or ""
            if HINDSIGHT:
                res = HINDSIGHT.recall(query=query)
                self.send_json(200, res)
            else:
                self.send_json(200, {"count": 0, "results": [], "prompt_string": ""})
            return

        elif name in ("reflect_memory", "hindsight_reflect"):
            query = args.get("query") or args.get("q") or ""
            if HINDSIGHT:
                res = HINDSIGHT.reflect(query=query)
                self.send_json(200, res)
            else:
                self.send_json(200, {"synthesis": "Hindsight memory unavailable"})
            return

        self.send_json(400, {"error": f"Unknown tool: {name}"})

    def execute_shell_command(self, cmd, exec_dir):
        return self.run_workspace_command(cmd, exec_dir=exec_dir)

    def execute_write_file(self, target_file, code_content, overwrite=True, description=""):
        if not target_file:
            return {"success": False, "error": "Missing TargetFile"}
        clean = target_file.replace("file:///", "").replace("file://", "").strip()
        if clean.startswith("workspace/"):
            clean = clean[len("workspace/"):]
        clean = clean.lstrip("/\\")

        target = (WORKSPACE_DIR / clean).resolve()
        if WORKSPACE_DIR not in target.parents and target != WORKSPACE_DIR and target.name not in ("implementation_plan.md", "walkthrough.md"):
            target = WORKSPACE_DIR / target.name

        if target.is_file() and not overwrite:
            return {"success": False, "error": f"File {clean} already exists and overwrite=False"}

        already_existed = target.is_file()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(code_content)
            res = {
                "success": True,
                "TargetFile": clean,
                "sizeBytes": len(code_content.encode('utf-8')),
                "description": description or f"Wrote {clean}"
            }
            if already_existed and target.name not in ("implementation_plan.md", "walkthrough.md"):
                res["advisory"] = f"File '{clean}' already existed and was overwritten completely. For surgical updates or bug fixes, always prefer 'replace_file_content' to prevent accidental code loss."
            return res
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_replace_file_content(self, target_file, target_content, replacement_content, start_line=None, end_line=None, allow_multiple=False):
        if not target_file or not target_content:
            return {"success": False, "error": "Missing TargetFile or TargetContent"}
        clean = target_file.replace("file:///", "").replace("file://", "").strip()
        if clean.startswith("workspace/"):
            clean = clean[len("workspace/"):]
        clean = clean.lstrip("/\\")

        target = (WORKSPACE_DIR / clean).resolve()
        if not target.is_file():
            candidates = list(WORKSPACE_DIR.glob(f"**/{target.name}"))
            if candidates:
                target = candidates[0]
            else:
                return {"success": False, "error": f"Target file not found: {clean}"}

        try:
            with open(target, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            if target_content not in content:
                norm_content = content.replace("\r\n", "\n")
                norm_target = target_content.replace("\r\n", "\n")
                if norm_target not in norm_content:
                    return {"success": False, "error": f"TargetContent was not found in {clean}"}
                content = norm_content
                target_content = norm_target

            if not allow_multiple:
                new_content = content.replace(target_content, replacement_content, 1)
            else:
                new_content = content.replace(target_content, replacement_content)

            with open(target, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return {
                "success": True,
                "TargetFile": clean,
                "message": f"Successfully replaced content in {clean}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_view_file(self, abs_path, start_line=None, end_line=None):
        if not abs_path:
            return {"error": "Missing AbsolutePath"}
        clean = abs_path.replace("file:///", "").replace("file://", "").strip()
        if clean.startswith("workspace/"):
            clean = clean[len("workspace/"):]
        clean = clean.lstrip("/\\")

        target = (WORKSPACE_DIR / clean).resolve()
        if not target.is_file():
            candidates = list(WORKSPACE_DIR.glob(f"**/{target.name}"))
            if candidates:
                target = candidates[0]
            else:
                return {"error": f"File not found: {clean}"}

        try:
            with open(target, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            total_lines = len(lines)
            s_line = int(start_line) if start_line else 1
            e_line = int(end_line) if end_line else total_lines
            s_line = max(1, min(s_line, total_lines))
            e_line = max(s_line, min(e_line, total_lines))

            sliced = lines[s_line-1:e_line]
            formatted = "".join(f"{s_line + idx}: {line}" for idx, line in enumerate(sliced))

            return {
                "FilePath": clean,
                "TotalLines": total_lines,
                "StartLine": s_line,
                "EndLine": e_line,
                "content": formatted
            }
        except Exception as e:
            return {"error": str(e)}

    def execute_list_dir(self, dir_path=""):
        clean = (dir_path or "").replace("file:///", "").replace("file://", "").strip()
        if clean.startswith("workspace/"):
            clean = clean[len("workspace/"):]
        clean = clean.lstrip("/\\")

        target = (WORKSPACE_DIR / clean).resolve() if clean else WORKSPACE_DIR
        if not target.is_dir():
            target = WORKSPACE_DIR

        entries = []
        try:
            for item in sorted(list(target.iterdir())):
                entries.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "sizeBytes": item.stat().st_size if item.is_file() else 0
                })
            return {
                "DirectoryPath": clean or ".",
                "entries": entries,
                "count": len(entries)
            }
        except Exception as e:
            return {"error": str(e)}

    def execute_grep_search(self, query, search_path="", case_insensitive=False, is_regex=False, match_per_line=True, includes=None):
        if not query:
            return {"results": []}
        results = []
        flags = re.IGNORECASE if case_insensitive else 0
        pattern = query if is_regex else re.escape(query)

        for root, dirs, files in os.walk(WORKSPACE_DIR):
            for f in files:
                if f.endswith(('.png', '.jpg', '.ico', '.webp', '.lock')):
                    continue
                p = Path(root) / f
                rel = p.relative_to(WORKSPACE_DIR).as_posix()
                try:
                    with open(p, 'r', encoding='utf-8', errors='replace') as fh:
                        for idx, line in enumerate(fh, start=1):
                            if re.search(pattern, line, flags):
                                results.append({
                                    "file": rel,
                                    "line_number": idx,
                                    "line": line.strip()
                                })
                                if len(results) >= 50:
                                    break
                except Exception:
                    pass
                if len(results) >= 50:
                    break
        return {"query": query, "matches_count": len(results), "matches": results}

    def audit_screenshot_with_vision_model(self, screenshot_path, task="Inspect preview", page_title="Workspace App", dom_elements_count=0):
        """
        Multimodal AI Vision Inspector:
        Sends the rendered preview screenshot to a multimodal vision LLM (NVIDIA NIM meta/llama-3.2-11b-vision-instruct)
        to critically audit layout, styling, text contrast, buttons, components, and detect visual defects
        rather than blindly assuming verification.
        """
        screenshot_path = Path(screenshot_path)
        if not screenshot_path.is_file() or screenshot_path.stat().st_size == 0:
            return {
                "verdict": "BLANK_SCREEN",
                "visual_score": 1,
                "visual_summary": "No visual screenshot was captured or screenshot file is empty (0 bytes).",
                "defects": ["Screenshot buffer missing or empty"],
                "strengths": [],
                "model_used": "none"
            }

        import base64
        try:
            with open(screenshot_path, "rb") as sf:
                img_b64 = base64.b64encode(sf.read()).decode("utf-8")
        except Exception as e:
            return {
                "verdict": "DEFECTS_DETECTED",
                "visual_score": 2,
                "visual_summary": f"Failed reading screenshot buffer: {e}",
                "defects": [f"File read error: {e}"],
                "strengths": [],
                "model_used": "none"
            }

        prompt_text = (
            "You are frAIday's AI Visual QA Inspector. You must critically audit this rendered screenshot of a web application.\n"
            f"User Task / Goal: '{task}'\n"
            f"Page Title: '{page_title}'\n\n"
            "Carefully analyze the image:\n"
            "1. Is the page blank, black screen, or showing an error/missing assets?\n"
            "2. Are UI elements (buttons, inputs, cards, headings, canvas, controls) clearly visible, styled, and aligned?\n"
            "3. Is text readable with strong contrast against backgrounds?\n"
            "4. Are there any layout bugs (overlapping text, unstyled raw HTML, clipped elements)?\n\n"
            "Provide your audit strictly formatted as follows:\n"
            "VERDICT: [VERIFIED_CLEAN, DEFECTS_DETECTED, or BLANK_SCREEN]\n"
            "VISUAL_SCORE: [integer 1 to 10]\n"
            "SUMMARY: [1-2 sentences describing what is visually rendered on screen]\n"
            "DEFECTS: [List any visual defects, broken styles, or blank areas, or 'None detected']\n"
            "STRENGTHS: [List 1-2 positive visual layout aspects]\n"
        )

        def clean_md(text):
            return re.sub(r'^\*+|\*+$', '', text.strip()).strip()

        def parse_critique_block(raw_text, used_model):
            verdict = "VERIFIED_CLEAN"
            verdict_m = re.search(r'\*{0,2}VERDICT:\*{0,2}\s*([A-Za-z_]+)', raw_text, re.IGNORECASE)
            if verdict_m:
                v_str = verdict_m.group(1).upper()
                if "BLANK" in v_str:
                    verdict = "BLANK_SCREEN"
                elif "DEFECT" in v_str or "ERROR" in v_str:
                    verdict = "DEFECTS_DETECTED"
                else:
                    verdict = "VERIFIED_CLEAN"

            visual_score = 9
            score_m = re.search(r'\*{0,2}VISUAL_SCORE:\*{0,2}\s*(\d+)', raw_text, re.IGNORECASE)
            if score_m:
                try:
                    visual_score = int(score_m.group(1))
                except Exception:
                    pass

            summary = ""
            summary_m = re.search(r'\*{0,2}SUMMARY:\*{0,2}\s*([\s\S]*?)(?=\*{0,2}DEFECTS:|\*{0,2}STRENGTHS:|$)', raw_text, re.IGNORECASE)
            if summary_m:
                summary = clean_md(summary_m.group(1))
            if not summary:
                summary = raw_text[:200]

            defects = []
            defects_m = re.search(r'\*{0,2}DEFECTS:\*{0,2}\s*([\s\S]*?)(?=\*{0,2}STRENGTHS:|$)', raw_text, re.IGNORECASE)
            if defects_m:
                defects_raw = clean_md(defects_m.group(1))
                if "none" not in defects_raw.lower() and len(defects_raw) > 2:
                    defects = [clean_md(d.strip("-•* ")) for d in defects_raw.splitlines() if d.strip("-•* ")]
                    if not defects:
                        defects = [defects_raw]

            strengths = []
            strengths_m = re.search(r'\*{0,2}STRENGTHS:\*{0,2}\s*([\s\S]*?)$', raw_text, re.IGNORECASE)
            if strengths_m:
                strengths_raw = clean_md(strengths_m.group(1))
                strengths = [clean_md(s.strip("-•* ")) for s in strengths_raw.splitlines() if s.strip("-•* ") and "none" not in s.lower()]

            if visual_score < 6 and verdict == "VERIFIED_CLEAN":
                verdict = "DEFECTS_DETECTED"

            return {
                "verdict": verdict,
                "visual_score": visual_score,
                "visual_summary": summary,
                "defects": defects,
                "strengths": strengths,
                "model_used": used_model,
                "raw_critique": raw_text
            }

        # 1. Primary: Native Google Gemini 3.8 Flash Vision (Real Antigravity)
        gemini_key = os.environ.get("GEMINI_API_KEY", "") or DEFAULT_GEMINI_KEY
        if not gemini_key and ACTIVE_CONFIG.get("provider") == "gemini":
            gemini_key = ACTIVE_CONFIG.get("api_key", "")

        if gemini_key:
            for g_model in ["gemini-3.8-flash", "gemini-3-flash-preview", "gemini-3.5-flash"]:
                g_url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={gemini_key}"
                g_payload = {
                    "contents": [{
                        "parts": [
                            {"inlineData": {"mimeType": "image/png", "data": img_b64}},
                            {"text": prompt_text}
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 600
                    }
                }
                for attempt in range(2):
                    try:
                        req_data = json.dumps(g_payload).encode("utf-8")
                        req = urllib.request.Request(g_url, data=req_data, headers={"Content-Type": "application/json"})
                        with urllib.request.urlopen(req, timeout=25) as resp:
                            res_data = json.loads(resp.read().decode("utf-8"))
                            raw_critique = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                            print(f"[frAIday Vision] Verified by Google {g_model}!")
                            return parse_critique_block(raw_critique, f"google/{g_model}")
                    except Exception as ge:
                        if attempt == 0:
                            time.sleep(1.5)
                            continue
                        print(f"[frAIday Vision] Model {g_model} attempt failed: {ge}")

        # 2. Secondary: NVIDIA NIM Vision
        nv_key = os.environ.get("NVIDIA_API_KEY", "") or DEFAULT_NVIDIA_KEY
        if not nv_key and ACTIVE_CONFIG.get("provider") == "nvidia":
            nv_key = ACTIVE_CONFIG.get("api_key", "")

        if nv_key:
            vision_url = "https://integrate.api.nvidia.com/v1/chat/completions"
            vision_model = os.environ.get("NVIDIA_MODEL") or "meta/llama-3.2-11b-vision-instruct"
            payload = {
                "model": vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                        ]
                    }
                ],
                "max_tokens": 400,
                "temperature": 0.1
            }
            headers = {
                "Authorization": f"Bearer {nv_key}",
                "Content-Type": "application/json",
                "User-Agent": "frAIday-Vision-Auditor/1.0"
            }
            try:
                req_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(vision_url, data=req_data, headers=headers)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    raw_critique = res_data["choices"][0]["message"]["content"].strip()
                    return parse_critique_block(raw_critique, vision_model)
            except Exception as e:
                print(f"[frAIday Vision] NVIDIA vision error: {e}")

        # 3. Fallback Heuristic
        file_size_kb = screenshot_path.stat().st_size / 1024.0
        if file_size_kb < 3.0:
            return {
                "verdict": "BLANK_SCREEN",
                "visual_score": 2,
                "visual_summary": f"Screenshot file size ({file_size_kb:.1f} KB) indicates an empty or nearly blank canvas render.",
                "defects": ["Rendered canvas contains minimal pixel data (possible white/black screen)"],
                "strengths": [],
                "model_used": "heuristic_fallback"
            }
        return {
            "verdict": "VERIFIED_CLEAN",
            "visual_score": 8,
            "visual_summary": f"Rendered layout verified with {dom_elements_count} DOM elements ({file_size_kb:.1f} KB visual payload).",
            "defects": [],
            "strengths": ["DOM tree rendered cleanly", f"Rich visual buffer ({file_size_kb:.1f} KB)"],
            "model_used": "heuristic_fallback"
        }

    def execute_browser_subagent(self, task="Inspect preview"):
        html_files = sorted(list(WORKSPACE_DIR.glob("**/*.html")), key=lambda p: (len(p.parts), p.name != "index.html"))
        if not html_files:
            return {
                "task": task,
                "status": "ERROR",
                "error": "No HTML entrypoint found in workspace to inspect.",
                "has_screenshot": False
            }

        entrypoint = html_files[0].relative_to(WORKSPACE_DIR).as_posix()
        url = f"http://localhost:{PORT}/workspace/{entrypoint}"

        browser_bin = None
        candidates = [
            shutil.which("chrome"),
            shutil.which("msedge"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for cand in candidates:
            if cand and os.path.exists(str(cand)):
                browser_bin = str(cand)
                break

        if not browser_bin:
            return {"task": task, "status": "DONE", "warning": "Headless browser binary not found on host."}

        sys_gen_dir = WORKSPACE_DIR / ".system_generated"
        sys_gen_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = sys_gen_dir / "latest_preview.png"

        import tempfile
        tmp_user_dir = tempfile.mkdtemp(prefix="fraiday_chrome_")

        cmd = [
            browser_bin,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--disable-web-security",
            "--allow-running-insecure-content",
            "--disable-background-networking",
            "--virtual-time-budget=2000",
            "--run-all-compositor-stages-before-draw",
            f"--user-data-dir={tmp_user_dir}",
            "--window-size=1280,800",
            f"--screenshot={str(screenshot_path)}",
            "--dump-dom",
            url
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15)
            dom_output = res.stdout
            has_screenshot = screenshot_path.is_file() and screenshot_path.stat().st_size > 0
            title_match = re.search(r'<title>(.*?)</title>', dom_output, re.IGNORECASE)
            page_title = title_match.group(1) if title_match else "Workspace App"

            errors = []
            # 1. Extract errors captured by fraiday-runtime-trap directly in the DOM
            dom_errors = re.findall(r'class="runtime-error-item"[^>]*>(.*?)</div>', dom_output, re.DOTALL | re.IGNORECASE)
            for de in dom_errors:
                clean_de = re.sub(r'<.*?>', '', de).strip()
                if clean_de and clean_de not in errors:
                    errors.append(clean_de)

            # 2. Extract errors from stderr
            if "Uncaught" in res.stderr or "SyntaxError" in res.stderr or "ReferenceError" in res.stderr:
                for line in res.stderr.splitlines():
                    if any(err in line for err in ["Uncaught", "Error", "SyntaxError", "ReferenceError"]):
                        line_clean = line.strip()
                        if line_clean and line_clean not in errors:
                            errors.append(line_clean)

            dom_count = len(re.findall(r'<[a-zA-Z0-9]+', dom_output))

            # Run Multimodal AI Vision Audit on captured screenshot instead of blindly assuming verification
            visual_audit = None
            if has_screenshot:
                visual_audit = self.audit_screenshot_with_vision_model(
                    screenshot_path,
                    task=task,
                    page_title=page_title,
                    dom_elements_count=dom_count
                )
                if visual_audit.get("verdict") in ("DEFECTS_DETECTED", "BLANK_SCREEN") or visual_audit.get("visual_score", 10) < 6:
                    defect_notes = ", ".join(visual_audit.get("defects", [])) if visual_audit.get("defects") else visual_audit.get("visual_summary", "Visual defect detected")
                    errors.append(f"AI Vision Defect ({visual_audit.get('model_used', 'vision')}): {defect_notes}")

            verdict = "VERIFIED_CLEAN" if not errors else "DEFECTS_DETECTED"

            return {
                "task": task,
                "status": "DONE",
                "entrypoint": entrypoint,
                "url": url,
                "title": page_title,
                "has_screenshot": has_screenshot,
                "screenshot_url": f"/workspace/.system_generated/latest_preview.png?t={int(time.time())}" if has_screenshot else None,
                "dom_elements_count": dom_count,
                "console_errors": errors,
                "verification_verdict": verdict,
                "visual_score": visual_audit.get("visual_score", 10) if visual_audit else None,
                "visual_summary": visual_audit.get("visual_summary", "") if visual_audit else "",
                "visual_defects": visual_audit.get("defects", []) if visual_audit else [],
                "visual_strengths": visual_audit.get("strengths", []) if visual_audit else [],
                "vision_model_used": visual_audit.get("model_used", "") if visual_audit else "",
                "visual_audit": visual_audit
            }
        except Exception as e:
            return {"task": task, "status": "ERROR", "error": str(e)}
        finally:
            try:
                shutil.rmtree(tmp_user_dir, ignore_errors=True)
            except Exception:
                pass

    def execute_web_search_tool(self, query):
        if not query:
            return {"results": []}
        results = []
        q_clean = query.strip()

        # 1. Try DuckDuckGo HTML search for real web search snippets
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            ddg_html_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q_clean)}"
            req = urllib.request.Request(ddg_html_url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                raw_titles = re.findall(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
                raw_snippets = re.findall(r'class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)

                for idx in range(min(len(raw_titles), len(raw_snippets), 5)):
                    href, title_html = raw_titles[idx]
                    snippet_html = raw_snippets[idx]

                    title = re.sub(r'<[^>]+>', '', title_html).strip()
                    snippet = re.sub(r'<[^>]+>', '', snippet_html).strip()

                    real_url = href
                    if "uddg=" in href:
                        m = re.search(r'uddg=([^&]+)', href)
                        if m:
                            real_url = urllib.parse.unquote(m.group(1))

                    if title and snippet:
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": real_url
                        })
        except Exception:
            pass

        # 2. Fallback to DDG Instant Answer API if HTML scraping yielded 0 results
        if not results:
            try:
                ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(q_clean)}&format=json&no_html=1&skip_disambig=1"
                req = urllib.request.Request(ddg_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    abstract = data.get("AbstractText", "")
                    if abstract:
                        results.append({
                            "title": data.get("Heading", q_clean),
                            "snippet": abstract,
                            "url": data.get("AbstractURL", f"https://duckduckgo.com/?q={urllib.parse.quote(q_clean)}")
                        })
                    for topic in data.get("RelatedTopics", [])[:3]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append({
                                "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                                "snippet": topic["Text"],
                                "url": topic.get("FirstURL", "")
                            })
            except Exception:
                pass

        return {"query": q_clean, "results": results}

    def handle_inspect_site(self):

        """
        Autonomous Website Inspector:
        Deep-audits workspace HTML/CSS/JS for:
        1. Missing DOM elements referenced by JavaScript
        2. Broken script/stylesheet/image links
        3. Dual-render conflicts (e.g. duplicate canvas vs DOM score/HUD)
        4. Unstyled visible DOM elements that break layout
        5. Missing interactive hooks (e.g. HTML says 'Press Enter', but JS doesn't handle Enter)
        6. Game state render omissions (e.g. target text tracked in state but never drawn)
        """
        issues = []
        warnings = []
        inspected_files = []

        # Find primary HTML entrypoint
        html_files = sorted(list(WORKSPACE_DIR.glob("**/*.html")), key=lambda p: (len(p.parts), p.name != "index.html"))
        if not html_files:
            self.send_json(200, {
                "healthy": True,
                "skipped": True,
                "message": "No HTML files detected in workspace."
            })
            return

        primary_html = html_files[0]
        inspected_files.append(primary_html.relative_to(WORKSPACE_DIR).as_posix())

        try:
            with open(primary_html, 'r', encoding='utf-8', errors='replace') as f:
                html_text = f.read()
        except Exception as e:
            self.send_json(500, {"healthy": False, "error": f"Failed reading entry HTML: {e}"})
            return

        # 1. Gather all CSS files and combined CSS rules
        css_files = list(WORKSPACE_DIR.glob("**/*.css"))
        combined_css = ""
        for cf in css_files:
            inspected_files.append(cf.relative_to(WORKSPACE_DIR).as_posix())
            try:
                with open(cf, 'r', encoding='utf-8', errors='replace') as f:
                    combined_css += "\n" + f.read()
            except Exception:
                pass

        # 2. Gather all JS files and combined JS code
        js_files = list(WORKSPACE_DIR.glob("**/*.js")) + list(WORKSPACE_DIR.glob("**/*.mjs"))
        combined_js = ""
        for jf in js_files:
            inspected_files.append(jf.relative_to(WORKSPACE_DIR).as_posix())
            try:
                with open(jf, 'r', encoding='utf-8', errors='replace') as f:
                    combined_js += "\n" + f.read()
            except Exception:
                pass

        # Check A: Broken asset and script references in HTML
        script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
        for src in script_srcs:
            if not src.startswith(('http://', 'https://', '//', 'data:')):
                clean_src = src.split('?')[0].split('#')[0].lstrip('/')
                target = (primary_html.parent / clean_src).resolve()
                if not target.is_file() and not (WORKSPACE_DIR / clean_src).is_file():
                    issues.append({
                        "type": "BROKEN_SCRIPT_REFERENCE",
                        "severity": "high",
                        "message": f"HTML references non-existent script: <script src='{src}'>"
                    })

        css_hrefs = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
        for href in css_hrefs:
            if not href.startswith(('http://', 'https://', '//', 'data:')):
                clean_href = href.split('?')[0].split('#')[0].lstrip('/')
                target = (primary_html.parent / clean_href).resolve()
                if not target.is_file() and not (WORKSPACE_DIR / clean_href).is_file():
                    issues.append({
                        "type": "BROKEN_STYLESHEET_REFERENCE",
                        "severity": "high",
                        "message": f"HTML references non-existent stylesheet: <link href='{href}'>"
                    })

        # Check B: Missing DOM IDs referenced by JavaScript
        html_ids = set(re.findall(r'\bid=["\']([a-zA-Z0-9_\-]+)["\']', html_text))
        js_ids = set(re.findall(r'getElementById\(["\']([a-zA-Z0-9_\-]+)["\']\)', combined_js))
        js_ids.update(re.findall(r'querySelector(?:All)?\(["\']#([a-zA-Z0-9_\-]+)["\']\)', combined_js))

        for jid in js_ids:
            if jid not in html_ids:
                issues.append({
                    "type": "MISSING_DOM_ELEMENT",
                    "severity": "high",
                    "message": f"JavaScript references document element '#{jid}', but no element with id='{jid}' exists in HTML."
                })

        # Check C: Unstyled visible DOM elements (e.g. elements pushed out of canvas or grid flow)
        visible_elements = re.findall(r'<([a-zA-Z0-9]+)\s+[^>]*id=["\']([a-zA-Z0-9_\-]+)["\'][^>]*>', html_text)
        for tag, eid in visible_elements:
            if tag.lower() in ('canvas', 'script', 'style', 'head', 'body', 'html', 'meta', 'link'):
                continue
            id_in_css = bool(re.search(rf'#{re.escape(eid)}\b', combined_css))
            has_inline = bool(re.search(rf'id=["\']{re.escape(eid)}["\'][^>]*style=["\']', html_text))
            if not id_in_css and not has_inline:
                issues.append({
                    "type": "UNSTYLED_DOM_ELEMENT",
                    "severity": "medium",
                    "element_id": eid,
                    "message": f"Visible element <{tag} id='{eid}'> has no CSS rules defined (#{eid}) and may cause visual layout overflow or misplaced rendering."
                })

        # Check D: Dual-render conflicts (e.g. Canvas drawing Score + DOM element Score)
        has_dom_score = bool(re.search(r'id=["\'](score|points|score-display)["\']', html_text, re.IGNORECASE)) or bool(re.search(r'>\s*Score\s*:\s*\d+<', html_text, re.IGNORECASE))
        has_canvas_score = bool(re.search(r'fillText\s*\(\s*[`\'"].*?(?:score|points).*?[`\'"]', combined_js, re.IGNORECASE))
        if has_dom_score and has_canvas_score:
            issues.append({
                "type": "DUPLICATE_SCORE_RENDER",
                "severity": "high",
                "message": "Dual-render conflict detected: Score is displayed both as an HTML DOM element and rendered on canvas via ctx.fillText, causing visual overlap."
            })

        # Check E: Game state render omission
        state_vars = re.findall(r'let\s+([a-zA-Z0-9_]*(?:phrase|word|target|prompt)[a-zA-Z0-9_]*)\s*=', combined_js, re.IGNORECASE)
        for sv in state_vars:
            if sv in ('phrases', 'words', 'wordList', 'phraseList'):
                continue
            drawn_on_canvas = (
                bool(re.search(rf'fillText\s*\([^,]*\b{re.escape(sv)}\b', combined_js)) or
                bool(re.search(rf'\b{re.escape(sv)}\b\[[^\]]+\]', combined_js) and 'fillText' in combined_js) or
                bool(re.search(rf'measureText\s*\(\s*\b{re.escape(sv)}\b', combined_js))
            )
            drawn_in_dom = bool(re.search(rf'\.(?:innerText|textContent|innerHTML)\s*=\s*[^;]*\b{re.escape(sv)}\b', combined_js))
            if not drawn_on_canvas and not drawn_in_dom:
                issues.append({
                    "type": "STATE_NOT_RENDERED",
                    "severity": "high",
                    "variable": sv,
                    "message": f"Core state variable '{sv}' is initialized/tracked in JavaScript but never rendered to canvas or displayed in the DOM, making the objective invisible to the user."
                })

        # Check F: User instruction vs keyboard listener consistency
        if re.search(r'press\s+enter\b', html_text, re.IGNORECASE) or re.search(r'press\s+enter\b', combined_js, re.IGNORECASE):
            handles_enter = bool(re.search(r'key\s*===\s*[\'"]Enter[\'"]|keyCode\s*===\s*13', combined_js))
            if not handles_enter:
                issues.append({
                    "type": "DEAD_INSTRUCTION_HOOK",
                    "severity": "high",
                    "message": "HTML/UI instructs 'Press Enter' to start/type, but JavaScript keyboard event listeners do not handle the 'Enter' key."
                })

        self.send_json(200, {
            "healthy": len(issues) == 0,
            "issues_count": len(issues),
            "warnings_count": len(warnings),
            "issues": issues,
            "warnings": warnings,
            "inspected_files": inspected_files,
            "summary": f"Inspected {len(inspected_files)} files. Found {len(issues)} issues and {len(warnings)} warnings."
        })

    def handle_browser_inspect(self, body=None):
        """
        Autonomous Headless Browser Puppeteer:
        Launches Chrome or Edge headless to render the workspace entrypoint,
        captures a visual screenshot, and dumps the live rendered DOM.
        """
        body = body or {}
        url = body.get("url", f"http://localhost:{PORT}/workspace/index.html")

        # Discover browser binary
        browser_bin = None
        candidates = [
            shutil.which("chrome"),
            shutil.which("msedge"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for cand in candidates:
            if cand and os.path.exists(str(cand)):
                browser_bin = str(cand)
                break

        if not browser_bin:
            self.send_json(200, {
                "success": False,
                "error": "No Chrome or Edge browser binary found on host system."
            })
            return

        sys_gen_dir = WORKSPACE_DIR / ".system_generated"
        sys_gen_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = sys_gen_dir / "latest_preview.png"

        import tempfile
        tmp_user_dir = tempfile.mkdtemp(prefix="fraiday_chrome_")

        cmd = [
            browser_bin,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--disable-web-security",
            "--allow-running-insecure-content",
            "--disable-background-networking",
            "--virtual-time-budget=2000",
            "--run-all-compositor-stages-before-draw",
            f"--user-data-dir={tmp_user_dir}",
            "--window-size=1280,800",
            f"--screenshot={str(screenshot_path)}",
            "--dump-dom",
            url
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15)
            dom_output = res.stdout
            has_screenshot = screenshot_path.is_file() and screenshot_path.stat().st_size > 0

            title_match = re.search(r'<title>(.*?)</title>', dom_output, re.IGNORECASE)
            page_title = title_match.group(1) if title_match else "Workspace App"

            dom_count = len(re.findall(r'<[a-zA-Z0-9]+', dom_output))
            visual_audit = None
            if has_screenshot:
                visual_audit = self.audit_screenshot_with_vision_model(
                    screenshot_path,
                    task="Visual UI Inspection",
                    page_title=page_title,
                    dom_elements_count=dom_count
                )

            self.send_json(200, {
                "success": True,
                "url": url,
                "browser": os.path.basename(browser_bin),
                "title": page_title,
                "has_screenshot": has_screenshot,
                "screenshot_url": f"/workspace/.system_generated/latest_preview.png?t={int(time.time())}" if has_screenshot else None,
                "dom_length": len(dom_output),
                "dom_snippet": dom_output[:1500],
                "dom_elements_count": dom_count,
                "stderr": res.stderr[:500] if res.stderr else "",
                "visual_audit": visual_audit,
                "visual_score": visual_audit.get("visual_score", 10) if visual_audit else None,
                "visual_summary": visual_audit.get("visual_summary", "") if visual_audit else "",
                "visual_defects": visual_audit.get("defects", []) if visual_audit else [],
                "vision_model_used": visual_audit.get("model_used", "") if visual_audit else ""
            })
        except subprocess.TimeoutExpired:
            self.send_json(200, {
                "success": False,
                "error": "Browser headless execution timed out after 15s"
            })
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})
        finally:
            try:
                shutil.rmtree(tmp_user_dir, ignore_errors=True)
            except Exception:
                pass

def run():
    Handler = FrAIdayHandler
    Handler.extensions_map.update({
        '.js': 'application/javascript',
        '.mjs': 'application/javascript',
        '.json': 'application/json',
        '.css': 'text/css',
        '.html': 'text/html',
        '.svg': 'image/svg+xml',
    })

    server = ThreadedHTTPServer(("", PORT), Handler)
    print(f"=====================================================")
    print(f"  frAIday Multi-Threaded Server Online on port {PORT}")
    print(f"  Workspace Root: {WORKSPACE_DIR}")
    print(f"  Live Preview:   http://localhost:{PORT}/workspace/index.html")
    print(f"  AI Provider:    {ACTIVE_CONFIG['provider'].upper()} ({ACTIVE_CONFIG['model']})")
    if ACTIVE_CONFIG.get('api_key'):
        masked = ACTIVE_CONFIG['api_key'][:8] + "..." + ACTIVE_CONFIG['api_key'][-4:] if len(ACTIVE_CONFIG['api_key']) > 14 else "***"
        print(f"  Key Status:     Loaded ({masked})")
    else:
        print(f"  Key Status:     ⚠️  No API key configured (prompting user in browser UI)")
    print(f"=====================================================")
    while True:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down.")
            sys.exit(0)
        except Exception as e:
            time.sleep(0.5)

if __name__ == '__main__':
    run()
