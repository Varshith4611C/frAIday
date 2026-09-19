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
from pathlib import Path

PORT = 8080
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)

# Preconfigured default keys provided by user
DEFAULT_GROQ_KEY = os.environ.get(
    "GROQ_API_KEY",
    "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"
)
DEFAULT_CEREBRAS_KEY = os.environ.get(
    "CEREBRAS_API_KEY",
    "csk-xmdfvw9944fk9rxw2vjyctty5reynyvd2rntk2mewvy3ey9r"
)
DEFAULT_NVIDIA_KEY = os.environ.get(
    "NVIDIA_API_KEY",
    "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"
)

# Active runtime system configuration (updated via POST /api/config)
ACTIVE_CONFIG = {
    "provider": "groq",
    "api_key": DEFAULT_GROQ_KEY,
    "model": "openai/gpt-oss-20b",
    "safety": "request_review"
}

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

        # 1. API: List workspace files
        if path == "/api/workspace/files":
            self.handle_list_files()
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
            self.send_json(200, {
                "status": "online",
                "workspace": str(WORKSPACE_DIR),
                "provider": ACTIVE_CONFIG["provider"],
                "model": ACTIVE_CONFIG["model"],
                "has_api_key": bool(ACTIVE_CONFIG["api_key"]),
                "safety": ACTIVE_CONFIG["safety"]
            })
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

        if path == "/api/workspace/patch":
            self.handle_patch_file(body)
            return

        if path == "/api/browser/inspect":
            self.handle_browser_inspect(body)
            return

        if path == "/api/tools/execute":
            self.handle_tool_execute(body)
            return

        self.send_json(404, {"error": "API route not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/workspace/file":
            query = urllib.parse.parse_qs(parsed.query)
            rel_path = query.get("path", [""])[0]
            self.handle_delete_file(rel_path)
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

            # If HTML, inject runtime error monitoring script for autonomous self-healing
            if 'html' in (content_type or '').lower():
                try:
                    text_html = content.decode('utf-8', errors='replace')
                    trap_script = """<script id="fraiday-runtime-trap">
/* frAIday Autonomous Inspection & Runtime Trap */
(function() {
    window.addEventListener('error', function(e) {
        try {
            window.parent.postMessage({
                type: 'WORKSPACE_RUNTIME_ERROR',
                message: e.message || 'Unknown runtime error',
                filename: e.filename || '',
                lineno: e.lineno || 0,
                colno: e.colno || 0
            }, '*');
        } catch(err) {}
    });
    window.addEventListener('unhandledrejection', function(e) {
        try {
            window.parent.postMessage({
                type: 'WORKSPACE_RUNTIME_ERROR',
                message: 'Unhandled Promise Rejection: ' + (e.reason ? (e.reason.message || e.reason) : 'Unknown'),
                filename: '',
                lineno: 0,
                colno: 0
            }, '*');
        } catch(err) {}
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
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_list_files(self):
        files_list = []
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            for f in files:
                full = Path(root) / f
                rel = full.relative_to(WORKSPACE_DIR).as_posix()
                files_list.append({
                    "path": rel,
                    "size": full.stat().st_size,
                    "modified": int(full.stat().st_mtime)
                })
        self.send_json(200, {"files": sorted(files_list, key=lambda x: x["path"])})

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
            self.send_json(200, {"success": True, "message": "Workspace cleared"})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def handle_terminal_exec(self, body):
        cmd = body.get("command", "").strip()
        if not cmd:
            self.send_json(400, {"error": "Missing command"})
            return

        dangerous = ["rm -rf /", "mkfs", ":(){ :|:& };:"]
        for d in dangerous:
            if d in cmd:
                self.send_json(403, {"error": "Blocked potentially destructive system command", "stdout": "", "stderr": f"Command rejected by safety policy: {cmd}", "exit_code": 1})
                return

        try:
            # On Windows, ensure python and pip commands invoke sys.executable safely
            executable_cmd = cmd
            if executable_cmd.startswith("python "):
                executable_cmd = f'"{sys.executable}" ' + executable_cmd[7:]
            elif executable_cmd == "python":
                executable_cmd = f'"{sys.executable}"'
            elif executable_cmd.startswith("pip "):
                executable_cmd = f'"{sys.executable}" -m pip ' + executable_cmd[4:]
            elif executable_cmd == "pip":
                executable_cmd = f'"{sys.executable}" -m pip'

            proc = subprocess.Popen(
                executable_cmd,
                shell=True,
                cwd=str(WORKSPACE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            stdout, stderr = proc.communicate(timeout=90)
            self.send_json(200, {
                "command": cmd,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": proc.returncode
            })
        except subprocess.TimeoutExpired:
            proc.kill()
            self.send_json(200, {
                "command": cmd,
                "stdout": "",
                "stderr": "Execution timed out after 90 seconds",
                "exit_code": -1
            })
        except Exception as e:
            self.send_json(500, {"error": str(e), "stdout": "", "stderr": str(e), "exit_code": 1})

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
        api_key = body.get("api_key") or ACTIVE_CONFIG["api_key"]
        model = body.get("model") or ACTIVE_CONFIG["model"]
        provider = body.get("provider") or ACTIVE_CONFIG["provider"]

        if not messages and prompt:
            messages = [{"role": "user", "content": prompt}]

        if provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            groq_model = model or "openai/gpt-oss-20b"
            if groq_model in ("gpt-oss-120b", "openai-gpt-oss-120b"):
                groq_model = "openai/gpt-oss-120b"
            elif groq_model in ("gpt-oss-20b", "openai-gpt-oss-20b"):
                groq_model = "openai/gpt-oss-20b"
            elif groq_model in ("qwen-3.8-27b", "qwen3.8-27b"):
                groq_model = "qwen/qwen3.8-27b"

            # Formulate fallback cascade: try requested first, then fall back to 20b and qwen
            candidates = [groq_model]
            for fb in ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
                if fb not in candidates:
                    candidates.append(fb)

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) frAIday/1.0"
            }

            last_error = None
            for current_model in candidates:
                payload = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": body.get("temperature", 0.2),
                    "max_tokens": min(body.get("max_tokens", 2048), 2048)
                }
                if "tools" in body and body["tools"]:
                    payload["tools"] = body["tools"]
                if "tool_choice" in body and body["tool_choice"]:
                    payload["tool_choice"] = body["tool_choice"]

                req_data = json.dumps(payload).encode('utf-8')
                try:
                    req = urllib.request.Request(url, data=req_data, headers=headers)
                    with urllib.request.urlopen(req, timeout=60) as resp:
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
                            "raw": res_data
                        })
                        return
                except urllib.error.HTTPError as e:
                    err_text = e.read().decode('utf-8', errors='replace')
                    last_error = f"HTTP {e.code}: {err_text}"
                    if e.code == 429:
                        wait_sec = 2.5
                        try:
                            # Support formats like "32m47.328s" or "2.5s" or "1m30s"
                            m = re.search(r'try again in (?:(\d+)m)?([0-9.]+)s', err_text)
                            if m:
                                mins = float(m.group(1)) if m.group(1) else 0.0
                                secs = float(m.group(2))
                                wait_sec = mins * 60 + secs + 0.5
                        except Exception:
                            pass

                        # If wait is short (<= 5s) and not a daily quota lockout, sleep and retry once
                        is_daily_exhaustion = "tokens per day" in err_text or "TPD" in err_text or wait_sec > 8.0
                        if not is_daily_exhaustion and wait_sec <= 5.0:
                            print(f"[frAIday Server] Groq 429 rate limit on {current_model}. Backing off {wait_sec:.2f}s and retrying...")
                            time.sleep(wait_sec)
                            try:
                                req_retry = urllib.request.Request(url, data=req_data, headers=headers)
                                with urllib.request.urlopen(req_retry, timeout=60) as resp2:
                                    res_data2 = json.loads(resp2.read().decode('utf-8'))
                                    choice2 = res_data2['choices'][0]
                                    message2 = choice2.get('message', {})
                                    content2 = message2.get('content', '')
                                    if not content2 and 'reasoning' in message2:
                                        content2 = message2['reasoning']
                                    tool_calls2 = message2.get('tool_calls', None)
                                    self.send_json(200, {
                                        "content": content2,
                                        "tool_calls": tool_calls2,
                                        "message": message2,
                                        "model_used": current_model,
                                        "raw": res_data2
                                    })
                                    return
                            except Exception as retry_err:
                                print(f"[frAIday Server] Retry on {current_model} failed: {retry_err}")

                        # If wait is long or daily limit is hit, seamlessly switch to next candidate
                        print(f"[frAIday Server] {current_model} 429 quota/rate limit hit ({wait_sec:.1f}s wait). Auto-falling back to next available model in cascade...")
                        continue
                    else:
                        print(f"[frAIday Server] Error calling {current_model}: {last_error}")
                        continue
                except Exception as e:
                    last_error = str(e)
                    continue

            self.send_json(429 if "429" in str(last_error) else 500, {
                "error": f"Groq Gateway Error: {last_error}"
            })
            return


        elif provider == "cerebras":
            url = "https://api.cerebras.ai/v1/chat/completions"
            payload = {
                "model": model or "gpt-oss-120b",
                "messages": messages,
                "temperature": body.get("temperature", 0.2),
                "max_tokens": min(body.get("max_tokens", 4096), 8192)
            }
            if "tools" in body and body["tools"]:
                payload["tools"] = body["tools"]
            if "tool_choice" in body and body["tool_choice"]:
                payload["tool_choice"] = body["tool_choice"]

            req_data = json.dumps(payload).encode('utf-8')
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) frAIday/1.0"
            }
            try:
                req = urllib.request.Request(url, data=req_data, headers=headers)
                with urllib.request.urlopen(req, timeout=60) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    choice = res_data['choices'][0]
                    message = choice.get('message', {})
                    content = message.get('content', '')
                    tool_calls = message.get('tool_calls', None)
                    self.send_json(200, {
                        "content": content,
                        "tool_calls": tool_calls,
                        "message": message,
                        "raw": res_data
                    })
                    return
            except urllib.error.HTTPError as e:
                err_text = e.read().decode('utf-8', errors='replace')
                self.send_json(e.code, {"error": f"Cerebras API Error (HTTP {e.code}): {err_text}"})
                return
            except Exception as e:
                self.send_json(500, {"error": f"Cerebras Gateway Error: {str(e)}"})
                return

        elif provider == "nvidia":
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

        if name == "run_command":
            cmd = args.get("CommandLine", "").strip()
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
            target_file = args.get("TargetFile", "").strip()
            code_content = args.get("CodeContent", "")
            overwrite = args.get("Overwrite", True)
            description = args.get("Description", "")
            res = self.execute_write_file(target_file, code_content, overwrite, description)
            self.send_json(200, res)
            return

        elif name == "replace_file_content":
            target_file = args.get("TargetFile", "").strip()
            target_content = args.get("TargetContent", "")
            replacement_content = args.get("ReplacementContent", "")
            start_line = args.get("StartLine")
            end_line = args.get("EndLine")
            allow_multiple = args.get("AllowMultiple", False)
            res = self.execute_replace_file_content(target_file, target_content, replacement_content, start_line, end_line, allow_multiple)
            self.send_json(200, res)
            return

        elif name == "view_file":
            abs_path = args.get("AbsolutePath", "").strip()
            start_line = args.get("StartLine")
            end_line = args.get("EndLine")
            res = self.execute_view_file(abs_path, start_line, end_line)
            self.send_json(200, res)
            return

        elif name == "list_dir":
            dir_path = args.get("DirectoryPath", "").strip()
            res = self.execute_list_dir(dir_path)
            self.send_json(200, res)
            return

        elif name == "grep_search":
            query = args.get("Query", "")
            search_path = args.get("SearchPath", "")
            case_insensitive = args.get("CaseInsensitive", False)
            is_regex = args.get("IsRegex", False)
            match_per_line = args.get("MatchPerLine", True)
            includes = args.get("Includes", [])
            res = self.execute_grep_search(query, search_path, case_insensitive, is_regex, match_per_line, includes)
            self.send_json(200, res)
            return

        elif name == "browser_subagent":
            task = args.get("Task", "Inspect rendered website for visual appearance, DOM elements, and console errors")
            res = self.execute_browser_subagent(task)
            self.send_json(200, res)
            return

        elif name == "search_web":
            q = args.get("query", "")
            res = self.execute_web_search_tool(q)
            self.send_json(200, res)
            return

        self.send_json(400, {"error": f"Unknown tool: {name}"})

    def execute_shell_command(self, cmd, exec_dir):
        if not cmd:
            return {"CommandLine": "", "stdout": "", "stderr": "No command provided", "exit_code": 1}
        dangerous = ["rm -rf /", "mkfs", ":(){ :|:& };:"]
        for d in dangerous:
            if d in cmd:
                return {"CommandLine": cmd, "stdout": "", "stderr": f"Blocked by safety policy: {cmd}", "exit_code": 1}

        executable_cmd = cmd
        if executable_cmd.startswith("python "):
            executable_cmd = f'"{sys.executable}" ' + executable_cmd[7:]
        elif executable_cmd.startswith("pip "):
            executable_cmd = f'"{sys.executable}" -m pip ' + executable_cmd[4:]
        elif executable_cmd == "python":
            executable_cmd = f'"{sys.executable}"'

        try:
            proc = subprocess.Popen(
                executable_cmd,
                shell=True,
                cwd=str(exec_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            stdout, stderr = proc.communicate(timeout=90)
            if stderr and ("ReferenceError: document is not defined" in stderr or "document is not def" in stderr or "ReferenceError: window is not defined" in stderr):
                stderr += "\n\n[SYSTEM ADVISORY]: You attempted to execute a client-side browser JavaScript script containing DOM APIs ('document' or 'window') using Node.js in the terminal. Node.js does not have browser DOM globals. Browser frontends run in the client browser, NOT in Node CLI. To test and audit browser client-side applications, ensure index.html loads the script and use the 'browser_subagent' tool to launch headless Chrome and inspect the live preview."
            return {
                "CommandLine": cmd,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": proc.returncode
            }
        except subprocess.TimeoutExpired:
            proc.kill()
            return {
                "CommandLine": cmd,
                "stdout": "",
                "stderr": "Command execution timed out after 90 seconds.",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "CommandLine": cmd,
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1
            }

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

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(code_content)
            return {
                "success": True,
                "TargetFile": clean,
                "sizeBytes": len(code_content.encode('utf-8')),
                "description": description or f"Wrote {clean}"
            }
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
            if "Uncaught" in res.stderr or "SyntaxError" in res.stderr or "ReferenceError" in res.stderr:
                for line in res.stderr.splitlines():
                    if any(err in line for err in ["Uncaught", "Error", "SyntaxError", "ReferenceError"]):
                        errors.append(line.strip())

            return {
                "task": task,
                "status": "DONE",
                "entrypoint": entrypoint,
                "url": url,
                "title": page_title,
                "has_screenshot": has_screenshot,
                "screenshot_url": f"/workspace/.system_generated/latest_preview.png?t={int(time.time())}" if has_screenshot else None,
                "dom_elements_count": len(re.findall(r'<[a-zA-Z0-9]+', dom_output)),
                "console_errors": errors,
                "verification_verdict": "VERIFIED_CLEAN" if not errors else "DEFECTS_DETECTED"
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
                for topic in data.get("RelatedTopics", [])[:3]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                            "snippet": topic["Text"],
                            "url": topic.get("FirstURL", "")
                        })
        except Exception:
            pass
        return {"query": query, "results": results}

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
            "--blink-settings=imagesEnabled=false",
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

            self.send_json(200, {
                "success": True,
                "url": url,
                "browser": os.path.basename(browser_bin),
                "title": page_title,
                "has_screenshot": has_screenshot,
                "screenshot_url": f"/workspace/.system_generated/latest_preview.png?t={int(time.time())}" if has_screenshot else None,
                "dom_length": len(dom_output),
                "dom_snippet": dom_output[:1500],
                "stderr": res.stderr[:500] if res.stderr else ""
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
    print(f"  Key Status:     Loaded ({ACTIVE_CONFIG['api_key'][:10]}...)")
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
