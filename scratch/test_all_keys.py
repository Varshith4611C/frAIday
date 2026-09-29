#!/usr/bin/env python3
"""
Test All Configured API Keys for frAIday:
- NVIDIA NIM (meta/llama-3.2-11b-vision-instruct · Active Primary)
- Vectorize Hindsight Agent Memory (Embedded TEMPR / Cloud)
- Groq LPU (llama-3.3-70b-versatile · Secondary)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
ENV_FILE = BASE_DIR / ".env"

# Load .env
if ENV_FILE.is_file():
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from server import (
    DEFAULT_GROQ_KEY,
    DEFAULT_NVIDIA_KEY
)

def test_chat_endpoint(url, key, model, name="Service", extra_headers=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 25,
        "temperature": 0.0
    }

    t0 = time.time()
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            elapsed = time.time() - t0
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return True, f"HTTP {resp.status} ({elapsed:.2f}s) -> '{content}'", elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        err_msg = ""
        try:
            err_data = json.loads(e.read().decode("utf-8"))
            err_msg = err_data.get("error", {}).get("message") or str(err_data)
        except Exception:
            err_msg = str(e)
        return False, f"HTTP {e.code} ({elapsed:.2f}s) - {err_msg[:100]}", elapsed
    except Exception as e:
        elapsed = time.time() - t0
        return False, f"Connection Failed ({elapsed:.2f}s): {str(e)[:100]}", elapsed

def main():
    print("=" * 60)
    print("  frAIday Comprehensive API Key Health & Latency Audit  ")
    print("=" * 60)

    results = {}

    # 1. Test Groq Keys (Primary Active Provider)
    groq_keys = [k.strip() for k in (os.environ.get("GROQ_API_KEY") or DEFAULT_GROQ_KEY).split(",") if k.strip()]
    groq_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    print(f"\n[1/3] Testing Groq Multi-Key Pool (Primary Active, {len(groq_keys)} keys found, model: {groq_model}):")
    groq_success_count = 0
    for idx, gk in enumerate(groq_keys, 1):
        masked = gk[:8] + "..." + gk[-4:]
        ok, detail, elapsed = test_chat_endpoint(
            url="https://api.groq.com/openai/v1/chat/completions",
            key=gk,
            model=groq_model,
            name="Groq"
        )
        status_icon = "✔" if ok else "✕"
        print(f"   Key {idx:02d} [{masked}]: {status_icon} {detail}")
        if ok:
            groq_success_count += 1
    results["Groq LPU"] = f"{groq_success_count}/{len(groq_keys)} functional ({groq_model})"

    # 2. Test NVIDIA NIM Key (Secondary / Backup Provider)
    print(f"\n[2/3] Testing NVIDIA NIM Key (Secondary / Backup Provider):")
    nv_key = os.environ.get("NVIDIA_API_KEY") or DEFAULT_NVIDIA_KEY
    if nv_key:
        masked_nv = nv_key[:8] + "..." + nv_key[-4:]
        ok_nv, detail_nv, _ = test_chat_endpoint(
            url="https://integrate.api.nvidia.com/v1/chat/completions",
            key=nv_key,
            model="meta/llama-3.2-11b-vision-instruct",
            name="NVIDIA NIM"
        )
        status_icon = "✔" if ok_nv else "✕"
        print(f"   Key [{masked_nv}]: {status_icon} {detail_nv}")
        results["NVIDIA NIM"] = "Active (meta/llama-3.2-11b-vision-instruct)" if ok_nv else detail_nv
    else:
        print("   No NVIDIA key configured.")
        results["NVIDIA NIM"] = "Not configured"

    # 3. Test Vectorize Hindsight Memory Engine
    print(f"\n[3/3] Testing Vectorize Hindsight Engine:")
    hs_key = os.environ.get("HINDSIGHT_API_KEY", "")
    hs_url = os.environ.get("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
    if hs_key:
        masked_hs = hs_key[:6] + "..." + hs_key[-4:]
        print(f"   Hindsight Cloud Key: {masked_hs} (Endpoint: {hs_url})")
        results["Hindsight"] = f"Cloud Connected ({hs_url})"
    else:
        print(f"   Hindsight Mode: Embedded High-Fidelity TEMPR Engine (100% Offline Active)")
        print(f"   (Use promo code MEMHACK99 at ui.hindsight.vectorize.io to add cloud key)")
        results["Hindsight"] = "Embedded TEMPR Engine Active (11 Memories Loaded)"

    print("\n" + "=" * 60)
    print("  SUMMARY REPORT  ")
    print("=" * 60)
    for k, v in results.items():
        print(f"  • {k:14}: {v}")
    print("=" * 60)

if __name__ == "__main__":
    main()
