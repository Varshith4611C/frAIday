#!/usr/bin/env python3
"""
Verification Script for frAIday + Vectorize Hindsight Integration
Tests:
1. Hindsight status endpoint
2. Memory Bank retrieval
3. Recall operation with TEMPR hybrid ranking
4. Retain operation for new observation and post-mortem
5. Reflect operation for synthesis
6. Memory tool execution via /api/tools/execute
"""

import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://localhost:8080"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

def post(path, data):
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

def run_tests():
    print("==================================================")
    print("  Testing frAIday + Vectorize Hindsight Backend   ")
    print("==================================================")

    # 1. Test Status
    try:
        status_code, data = get("/api/hindsight/status")
        print(f"1. Status Endpoint: HTTP {status_code}")
        print(f"   Engine: {data.get('engine')}")
        print(f"   Bank ID: {data.get('bank_id')}")
        print(f"   Stats: {json.dumps(data.get('stats'))}")
        assert status_code == 200, "Status endpoint returned non-200"
    except Exception as e:
        print(f"FAILED on status check: {e}")
        return False

    # 2. Test Bank Explorer
    try:
        status_code, data = get("/api/hindsight/bank")
        print(f"\n2. Bank Explorer Endpoint: HTTP {status_code}")
        bank = data.get("bank", {})
        print(f"   Mental Models: {len(bank.get('mental_models', []))}")
        print(f"   Observations: {len(bank.get('observations', []))}")
        print(f"   Incidents: {len(bank.get('experience_facts', []))}")
        print(f"   World Facts: {len(bank.get('world_facts', []))}")
        assert len(bank.get('mental_models', [])) > 0, "No mental models in bank"
    except Exception as e:
        print(f"FAILED on bank check: {e}")
        return False

    # 3. Test TEMPR Recall (Database Port scenario)
    try:
        query = "Configure postgres database connection and port"
        status_code, data = post("/api/hindsight/recall", {"query": query})
        print(f"\n3. TEMPR Recall for '{query}': HTTP {status_code}")
        print(f"   Recalled items count: {data.get('count')}")
        results = data.get("results", [])
        for r in results[:3]:
            print(f"   • [{r['tier'].upper()}] Score {r['score']}: {r['text'][:80]}...")
        assert data.get('count', 0) > 0, "No memories recalled for database query"
    except Exception as e:
        print(f"FAILED on recall check: {e}")
        return False

    # 4. Test Retain (New Rule)
    try:
        retain_data = {
            "memory_type": "mental_model",
            "content": "Always configure pytest with asyncio_mode=auto in pyproject.toml.",
            "metadata": {"title": "Pytest Asyncio Directive"},
            "tags": ["pytest", "asyncio", "python"]
        }
        status_code, data = post("/api/hindsight/retain", retain_data)
        print(f"\n4. Retain New Rule: HTTP {status_code}")
        print(f"   Retain result: {data.get('success')}")
        assert data.get('success') is True, "Retain failed"
    except Exception as e:
        print(f"FAILED on retain check: {e}")
        return False

    # 5. Test Reflect
    try:
        status_code, data = post("/api/hindsight/reflect", {"query": "database connection guidelines"})
        print(f"\n5. Hindsight Reflect Synthesis: HTTP {status_code}")
        print(f"   Synthesis snippet:\n   {data.get('synthesis', '')[:200]}...")
        assert "synthesis" in data, "No synthesis in reflect result"
    except Exception as e:
        print(f"FAILED on reflect check: {e}")
        return False

    # 6. Test Tool Execution (/api/tools/execute)
    try:
        tool_payload = {
            "name": "recall_memory",
            "arguments": {"query": "postgres port"}
        }
        status_code, data = post("/api/tools/execute", tool_payload)
        print(f"\n6. Tool Execute 'recall_memory': HTTP {status_code}")
        print(f"   Tool result count: {data.get('count')}")
        assert data.get('count', 0) > 0, "Tool execute recall failed"
    except Exception as e:
        print(f"FAILED on tool execute check: {e}")
        return False

    print("\n==================================================")
    print("  ALL 6 HINDSIGHT INTEGRATION TESTS PASSED!       ")
    print("==================================================")
    return True

if __name__ == "__main__":
    run_tests()
