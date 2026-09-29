#!/usr/bin/env python3
"""
frAIday — Vectorize Hindsight Native Memory Service
Implements Retain, Recall, and Reflect operations for Autonomous Agents.

Supports:
1. Live Hindsight Cloud (https://api.hindsight.vectorize.io) with HINDSIGHT_API_KEY
2. Local Docker Hindsight instance (http://localhost:8888)
3. Embedded High-Fidelity Hindsight Engine (Zero-configuration offline fallback with
   4-tier memory hierarchy: Mental Models, Observations, World Facts, Experience Facts,
   TEMPR multi-strategy hybrid retrieval, and persistent JSON bank storage)
"""

import os
import sys
import json
import time
import math
import re
from pathlib import Path
from datetime import datetime

try:
    from hindsight_client import Hindsight
    HAS_HINDSIGHT_SDK = True
except ImportError:
    HAS_HINDSIGHT_SDK = False

BASE_DIR = Path(__file__).resolve().parent
HINDSIGHT_DATA_FILE = BASE_DIR / ".fraiday_hindsight_bank.json"

DEFAULT_BANK_ID = os.environ.get("HINDSIGHT_BANK_ID", "fraiday-core-memory")
DEFAULT_BASE_URL = os.environ.get("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
DEFAULT_API_KEY = os.environ.get("HINDSIGHT_API_KEY", "")


class EmbeddedHindsightEngine:
    """
    High-fidelity embedded simulation of Vectorize Hindsight:
    - 4-Tier Memory Hierarchy:
      1. mental_models (Rules, playbooks, procedures)
      2. observations (Consolidated beliefs with proof counts & quotes)
      3. world_facts (Objective facts about repo, env, config)
      4. experience_facts (Execution logs, terminal post-mortems, bug patches)
    - TEMPR Multi-Strategy Hybrid Retrieval (Temporal, Entity, Matching, Proximity, Ranking)
    - Reflect reasoning synthesis
    """

    def __init__(self, storage_path=HINDSIGHT_DATA_FILE):
        self.storage_path = Path(storage_path)
        self.banks = {}
        self._load()

    def _load(self):
        if self.storage_path.is_file():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.banks = json.load(f)
            except Exception as e:
                print(f"[HindsightEngine] Warning: Failed to load storage: {e}")
                self.banks = {}
        if not self.banks or DEFAULT_BANK_ID not in self.banks:
            self._ensure_bank(DEFAULT_BANK_ID)

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.banks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[HindsightEngine] Warning: Failed to save storage: {e}")

    def _ensure_bank(self, bank_id):
        if bank_id not in self.banks:
            self.banks[bank_id] = {
                "id": bank_id,
                "name": "frAIday Codebase & Incident Memory Bank",
                "created_at": datetime.now().isoformat(),
                "mental_models": [],
                "observations": [],
                "world_facts": [],
                "experience_facts": [],
                "audit_log": []
            }
            self._save()
        return self.banks[bank_id]

    def _seed_default_bank(self, bank_id, force=False):
        if bank_id in self.banks and not force and any(self.banks[bank_id].get(k) for k in ("mental_models", "observations")):
            return

        now = datetime.now().isoformat()
        self.banks[bank_id] = {
            "id": bank_id,
            "name": "frAIday Codebase & Incident Memory Bank",
            "created_at": now,
            "mental_models": [
                {
                    "id": "mm-db-config",
                    "title": "Database Connection & Port Convention",
                    "directive": "When configuring PostgreSQL or database connections in this project, ALWAYS use host 'localhost' on port 5433 with sslmode=disable. The default 5432 is reserved for host services and will cause connection refusal.",
                    "applies_to": ["database", "postgres", "connection", "sql", "migration", "env"],
                    "confidence": 0.98,
                    "updated_at": now
                },
                {
                    "id": "mm-pydantic-v2",
                    "title": "Modern Pydantic v2 Syntax Standard",
                    "directive": "Never use Pydantic v1 patterns (class Config, .dict(), regex=). Always use Pydantic v2 syntax: model_config = ConfigDict(from_attributes=True), .model_dump(), and pattern= parameter in Field.",
                    "applies_to": ["pydantic", "models", "validation", "schema", "fastapi"],
                    "confidence": 0.95,
                    "updated_at": now
                },
                {
                    "id": "mm-devops-cors",
                    "title": "Workspace Web Server CORS & Health Protocol",
                    "directive": "Every backend API service created in ./workspace/ must include Access-Control-Allow-Origin: * headers on all endpoints (and handle OPTIONS) to enable preview in the frAIday workspace iframe. Include a /health endpoint.",
                    "applies_to": ["cors", "server", "http", "api", "preview", "iframe"],
                    "confidence": 0.99,
                    "updated_at": now
                }
            ],
            "observations": [
                {
                    "id": "obs-port-5433",
                    "fact": "Local Docker Compose Postgres service is mapped to host port 5433 to avoid port collision with host PostgreSQL 15.",
                    "proof_count": 4,
                    "quotes": [
                        "docker-compose.yml: ports: - '5433:5432'",
                        "Incident #104 post-mortem: verified connection succeeded only on 5433"
                    ],
                    "tags": ["postgres", "port", "docker", "incident"],
                    "last_verified": now
                },
                {
                    "id": "obs-es-modules",
                    "fact": "Frontend JavaScript files in this workspace use native ES Modules (import/export syntax) and do not support CommonJS require() without a bundler.",
                    "proof_count": 3,
                    "quotes": [
                        "index.html loads app.js as type='module'",
                        "Browser puppet test threw ReferenceError: require is not defined"
                    ],
                    "tags": ["javascript", "esm", "frontend"],
                    "last_verified": now
                },
                {
                    "id": "obs-alembic-upgrade",
                    "fact": "Database schema updates must be applied via 'alembic upgrade head' before running backend integration tests.",
                    "proof_count": 2,
                    "quotes": [
                        "pytest failed with sqlite3.OperationalError: no such table: users until alembic head was executed."
                    ],
                    "tags": ["alembic", "database", "migrations", "tests"],
                    "last_verified": now
                }
            ],
            "world_facts": [
                {
                    "id": "wf-tech-stack",
                    "fact": "The workspace uses Python 3.11+ for backend APIs and Vanilla JS + CSS for frontend components.",
                    "source": "repository_inspection",
                    "tags": ["stack", "python", "javascript"],
                    "timestamp": now
                },
                {
                    "id": "wf-env-secrets",
                    "fact": "Sensitive credentials are saved to .env and never committed to version control.",
                    "source": "security_policy",
                    "tags": ["security", "env"],
                    "timestamp": now
                }
            ],
            "experience_facts": [
                {
                    "id": "exp-incident-104",
                    "incident_id": "INC-104",
                    "title": "ConnectionRefusedError on Postgres Port 5432",
                    "root_cause": "Agent assumed standard 5432 port, but container was listening on 5433.",
                    "resolution": "Updated DATABASE_URL=postgresql://postgres:postgres@localhost:5433/dev_db?sslmode=disable",
                    "status": "resolved_and_verified",
                    "timestamp": now
                },
                {
                    "id": "exp-alembic-fix",
                    "incident_id": "INC-108",
                    "title": "Missing Table Users in Test Suite",
                    "root_cause": "Migration script generated but never applied to test database.",
                    "resolution": "Executed 'alembic upgrade head' as pre-test step in test runner.",
                    "status": "resolved_and_verified",
                    "timestamp": now
                }
            ],
            "audit_log": [
                {"action": "seed", "timestamp": now, "details": "Initialized Hindsight memory bank with codebase conventions."}
            ]
        }
        self._save()

    def retain(self, bank_id, content, memory_type="observation", metadata=None, tags=None, context=None):
        """
        Retain new structured memory into the bank:
        Deconstructs content and categorizes it into the appropriate memory tier.
        """
        bank = self._ensure_bank(bank_id)
        metadata = metadata or {}
        tags = tags or []
        now = datetime.now().isoformat()
        item_id = f"mem-{int(time.time() * 1000)}"

        # Auto-extract tags from content if none provided
        if not tags and isinstance(content, str):
            words = re.findall(r'[a-zA-Z0-9_\-\.]{3,}', content.lower())
            freq = {}
            for w in words:
                if w not in ("this", "that", "with", "from", "when", "always", "must", "have", "been"):
                    freq[w] = freq.get(w, 0) + 1
            tags = [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:6]]

        # Determine target tier
        content_lower = content.lower() if isinstance(content, str) else json.dumps(content).lower()
        is_preference = any(kw in content_lower for kw in ("prefer", "preference", "like", "dislike", "theme", "color", "styling", "dont like", "only like"))
        if memory_type == "mental_model" or is_preference or "always" in content_lower or "rule:" in content_lower or "never" in content_lower:
            if is_preference:
                for t in ("ui", "theme", "styling", "preference", "design", "all"):
                    if t not in tags:
                        tags.append(t)
            new_item = {
                "id": f"mm-{item_id}",
                "title": metadata.get("title", "User Aesthetic & Theme Directive" if is_preference else "Learned Behavioral Rule"),
                "directive": str(content),
                "applies_to": tags,
                "confidence": float(metadata.get("confidence", 0.99 if is_preference else 0.95)),
                "updated_at": now
            }
            bank["mental_models"].append(new_item)
            assigned_type = "mental_model"

        elif memory_type == "experience_fact" or "incident" in content_lower or "error" in content_lower or "fix" in content_lower:
            new_item = {
                "id": f"exp-{item_id}",
                "incident_id": metadata.get("incident_id", f"INC-{int(time.time()) % 10000}"),
                "title": metadata.get("title", "Execution Post-Mortem & Fix"),
                "root_cause": metadata.get("root_cause", str(content)),
                "resolution": metadata.get("resolution", str(content)),
                "status": "resolved_and_verified",
                "timestamp": now,
                "tags": tags
            }
            bank["experience_facts"].append(new_item)
            assigned_type = "experience_fact"

        elif memory_type == "world_fact":
            new_item = {
                "id": f"wf-{item_id}",
                "fact": str(content),
                "source": metadata.get("source", "agent_observation"),
                "tags": tags,
                "timestamp": now
            }
            bank["world_facts"].append(new_item)
            assigned_type = "world_fact"

        else:
            # Observation: deduplicate or update proof count
            matched_obs = None
            for obs in bank["observations"]:
                # Check for high token overlap
                obs_words = set(re.findall(r'\w+', obs["fact"].lower()))
                new_words = set(re.findall(r'\w+', content_lower))
                if obs_words and new_words:
                    jaccard = len(obs_words & new_words) / len(obs_words | new_words)
                    if jaccard > 0.45:
                        matched_obs = obs
                        break

            if matched_obs:
                matched_obs["proof_count"] = matched_obs.get("proof_count", 1) + 1
                matched_obs["last_verified"] = now
                if context and context not in matched_obs.get("quotes", []):
                    matched_obs.setdefault("quotes", []).append(context)
                new_item = matched_obs
                assigned_type = "observation_updated"
            else:
                new_item = {
                    "id": f"obs-{item_id}",
                    "fact": str(content),
                    "proof_count": 1,
                    "quotes": [context] if context else [],
                    "tags": tags,
                    "last_verified": now
                }
                bank["observations"].append(new_item)
                assigned_type = "observation"

        bank.setdefault("audit_log", []).append({
            "action": "retain",
            "type": assigned_type,
            "id": new_item.get("id"),
            "timestamp": now
        })
        self._save()

        return {
            "success": True,
            "operation": "retain",
            "bank_id": bank_id,
            "item_id": new_item.get("id"),
            "memory_type": assigned_type,
            "item": new_item
        }

    def recall(self, bank_id, query, types=None, max_tokens=2048, budget="mid"):
        """
        TEMPR Multi-Strategy Hybrid Recall:
        - BM25 & Keyword matching
        - Entity & Tag matching
        - Temporal recency weighting
        - Hierarchy prioritization: Mental Models > Observations > World Facts > Experience Facts
        """
        bank = self._ensure_bank(bank_id)
        query_lower = query.lower()
        query_tokens = set(re.findall(r'[a-zA-Z0-9_\-\.]{2,}', query_lower))

        # TEMPR Semantic Expansion: If query creates/builds an app or UI, expand to UI, design & preference concepts
        ui_triggers = {"create", "build", "make", "app", "ui", "calculator", "dashboard", "page", "website", "site", "component", "frontend", "design", "tool", "game", "view", "portal", "screen", "timer", "todo", "terminal"}
        is_ui_query = bool(query_tokens & ui_triggers)
        if is_ui_query:
            query_tokens.update({"ui", "design", "theme", "styling", "frontend", "color", "style", "css", "preference", "preferences"})

        ranked_results = []

        def score_text(text, tags=None, proof_count=1, recency_iso=None):
            if not text:
                return 0.0
            t_lower = text.lower()
            t_tokens = set(re.findall(r'[a-zA-Z0-9_\-\.]{2,}', t_lower))
            if not t_tokens:
                return 0.0

            # 1. Exact phrase boost
            exact_boost = 2.5 if query_lower in t_lower else 1.0

            # 2. Token overlap score (BM25 surrogate)
            overlap = len(query_tokens & t_tokens)
            token_score = (overlap / (math.sqrt(len(query_tokens)) * math.sqrt(len(t_tokens)) + 1e-5)) * 10.0

            # 3. Tag score
            tag_score = 0.0
            if tags:
                for tag in tags:
                    if tag.lower() in query_tokens:
                        tag_score += 3.0

            # 4. Proof count confidence boost
            proof_boost = 1.0 + math.log10(max(1, proof_count)) * 0.5

            # 5. Temporal recency factor
            recency_boost = 1.0
            if recency_iso:
                try:
                    dt = datetime.fromisoformat(recency_iso)
                    age_hours = (datetime.now() - dt).total_seconds() / 3600.0
                    recency_boost = max(0.8, 1.0 / (1.0 + age_hours * 0.01))
                except Exception:
                    pass

            final_score = (token_score + tag_score) * exact_boost * proof_boost * recency_boost
            return final_score

        # 1. Recall Mental Models (Highest Priority)
        if not types or "mental_models" in types or "mental_model" in types:
            for mm in bank.get("mental_models", []):
                score = score_text(mm.get("title", "") + " " + mm.get("directive", ""), mm.get("applies_to"), proof_count=5)
                mm_applies = [t.lower() for t in mm.get("applies_to", [])]
                is_pref_model = any(k in mm_applies for k in ("preference", "theme", "ui", "color", "styling", "all")) or "preference" in mm.get("title", "").lower() or "theme" in mm.get("title", "").lower()
                
                # Boost mental models baseline or if it's a UI/theme preference on a UI query
                if score > 0.4 or any(tag.lower() in query_lower for tag in mm.get("applies_to", [])) or (is_ui_query and is_pref_model):
                    ranked_results.append({
                        "tier": "mental_model",
                        "id": mm["id"],
                        "score": round(score + 10.0 if (is_ui_query and is_pref_model) else score + 5.0, 2),
                        "title": mm.get("title"),
                        "text": mm.get("directive"),
                        "metadata": {"confidence": mm.get("confidence", 0.95), "applies_to": mm.get("applies_to")}
                    })

        # 2. Recall Observations
        if not types or "observations" in types or "observation" in types:
            for obs in bank.get("observations", []):
                score = score_text(obs.get("fact", ""), obs.get("tags"), proof_count=obs.get("proof_count", 1), recency_iso=obs.get("last_verified"))
                if score > 0.5:
                    ranked_results.append({
                        "tier": "observation",
                        "id": obs["id"],
                        "score": round(score + 3.0, 2),
                        "title": f"Observation ({obs.get('proof_count', 1)} proofs)",
                        "text": obs.get("fact"),
                        "metadata": {"proof_count": obs.get("proof_count", 1), "quotes": obs.get("quotes", [])}
                    })

        # 3. Recall World Facts
        if not types or "world_facts" in types or "world_fact" in types:
            for wf in bank.get("world_facts", []):
                score = score_text(wf.get("fact", ""), wf.get("tags"), proof_count=1, recency_iso=wf.get("timestamp"))
                if score > 0.5:
                    ranked_results.append({
                        "tier": "world_fact",
                        "id": wf["id"],
                        "score": round(score + 1.0, 2),
                        "title": "World Fact",
                        "text": wf.get("fact"),
                        "metadata": {"source": wf.get("source")}
                    })

        # 4. Recall Experience Facts (Post-Mortems)
        if not types or "experience_facts" in types or "experience_fact" in types:
            for exp in bank.get("experience_facts", []):
                combined = f"{exp.get('title', '')} {exp.get('root_cause', '')} {exp.get('resolution', '')}"
                score = score_text(combined, exp.get("tags"), proof_count=2, recency_iso=exp.get("timestamp"))
                combined_lower = combined.lower()
                is_pref_exp = any(k in combined_lower for k in ("theme", "blue", "color", "preference", "dont like", "only like"))
                if score > 0.5 or (is_ui_query and is_pref_exp):
                    ranked_results.append({
                        "tier": "experience_fact",
                        "id": exp["id"],
                        "score": round(score + 6.0 if is_pref_exp else score + 2.0, 2),
                        "title": f"Incident Post-Mortem [{exp.get('incident_id')}]",
                        "text": f"Root Cause: {exp.get('root_cause')} | Resolution: {exp.get('resolution')}",
                        "metadata": {"incident_id": exp.get("incident_id"), "status": exp.get("status")}
                    })

        # Sort by score descending
        ranked_results.sort(key=lambda r: r["score"], reverse=True)

        # Build prompt injection string
        prompt_lines = []
        if ranked_results:
            prompt_lines.append("### 🧠 HINDSIGHT RECALLED MEMORY & REPOSITORY PLAYBOOK:")
            prompt_lines.append("The following knowledge, rules, and incident resolutions have been retained from previous interactions:\n")
            for idx, r in enumerate(ranked_results[:6], 1):
                tier_badge = r["tier"].upper().replace("_", " ")
                prompt_lines.append(f"{idx}. [{tier_badge}] {r['title']}: {r['text']}")
            prompt_lines.append("\nCRITICAL DIRECTIVE: You MUST respect these recalled rules and past resolutions. Do NOT repeat previous mistakes or violate conventions.\n")

        prompt_string = "\n".join(prompt_lines)

        return {
            "query": query,
            "bank_id": bank_id,
            "count": len(ranked_results),
            "results": ranked_results[:8],
            "prompt_string": prompt_string
        }

    def reflect(self, bank_id, query):
        """
        Synthesizes an evidence-grounded response reasoning over all 4 tiers of memory.
        """
        recall_res = self.recall(bank_id, query)
        results = recall_res.get("results", [])

        if not results:
            return {
                "query": query,
                "bank_id": bank_id,
                "synthesis": "No memories matching this query were found in Hindsight bank. The agent operates on standard zero-shot behavior.",
                "supporting_facts_count": 0
            }

        directives = [r["text"] for r in results if r["tier"] == "mental_model"]
        observations = [r["text"] for r in results if r["tier"] == "observation"]
        incidents = [r["text"] for r in results if r["tier"] == "experience_fact"]

        synthesis_parts = []
        if directives:
            synthesis_parts.append(f"**Governing Rules & Directives:**\n" + "\n".join(f"- {d}" for d in directives))
        if observations:
            synthesis_parts.append(f"**Verified Evidence & Observations:**\n" + "\n".join(f"- {o}" for o in observations))
        if incidents:
            synthesis_parts.append(f"**Past Incident Resolutions:**\n" + "\n".join(f"- {inc}" for inc in incidents))

        full_synthesis = "\n\n".join(synthesis_parts)
        return {
            "query": query,
            "bank_id": bank_id,
            "synthesis": full_synthesis,
            "supporting_facts_count": len(results),
            "top_memories": results[:5]
        }

    def get_bank_summary(self, bank_id):
        bank = self._ensure_bank(bank_id)
        return {
            "id": bank["id"],
            "name": bank.get("name", "frAIday Codebase Memory"),
            "created_at": bank.get("created_at"),
            "stats": {
                "mental_models": len(bank.get("mental_models", [])),
                "observations": len(bank.get("observations", [])),
                "world_facts": len(bank.get("world_facts", [])),
                "experience_facts": len(bank.get("experience_facts", [])),
                "total": (
                    len(bank.get("mental_models", [])) +
                    len(bank.get("observations", [])) +
                    len(bank.get("world_facts", [])) +
                    len(bank.get("experience_facts", []))
                )
            },
            "bank": bank
        }

    def reset_scenarios(self, bank_id):
        return self.clear_bank(bank_id)

    def clear_bank(self, bank_id):
        bank = self._ensure_bank(bank_id)
        now = datetime.now().isoformat()
        self.banks[bank_id] = {
            "id": bank_id,
            "name": "frAIday Codebase & Incident Memory Bank",
            "created_at": now,
            "mental_models": [],
            "observations": [],
            "world_facts": [],
            "experience_facts": [],
            "audit_log": [
                {"action": "clear", "timestamp": now, "details": "Cleared all memories from bank."}
            ]
        }
        self._save()
        return self.get_bank_summary(bank_id)


class HindsightService:
    """
    Unified Hindsight Manager:
    Automatically uses Vectorize Hindsight Cloud or local server if configured;
    smoothly falls back to EmbeddedHindsightEngine for 100% offline stability.
    """

    def __init__(self, base_url=DEFAULT_BASE_URL, api_key=DEFAULT_API_KEY, bank_id=DEFAULT_BANK_ID):
        self.base_url = base_url
        self.api_key = api_key
        self.bank_id = bank_id
        self.embedded = EmbeddedHindsightEngine()
        self.cloud_client = None
        self._init_cloud_client()

    def _init_cloud_client(self):
        if HAS_HINDSIGHT_SDK and self.api_key:
            try:
                self.cloud_client = Hindsight(base_url=self.base_url, api_key=self.api_key, timeout=15.0)
                print(f"[HindsightService] Initialized Hindsight Cloud Client connected to {self.base_url}")
            except Exception as e:
                print(f"[HindsightService] Notice: Cloud client init failed ({e}), using embedded engine.")
                self.cloud_client = None
        else:
            self.cloud_client = None

    def update_config(self, base_url=None, api_key=None, bank_id=None):
        if base_url:
            self.base_url = base_url
        if api_key is not None:
            self.api_key = api_key
        if bank_id:
            self.bank_id = bank_id
        self._init_cloud_client()

    def get_status(self):
        is_cloud_active = self.cloud_client is not None
        summary = self.embedded.get_bank_summary(self.bank_id)
        return {
            "status": "online",
            "engine": "hindsight_cloud" if is_cloud_active else "embedded_hindsight_engine",
            "is_cloud_active": is_cloud_active,
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
            "bank_id": self.bank_id,
            "sdk_available": HAS_HINDSIGHT_SDK,
            "stats": summary["stats"]
        }

    def retain(self, content, bank_id=None, memory_type="observation", metadata=None, tags=None, context=None):
        target_bank = bank_id or self.bank_id
        # Always retain locally in embedded engine for instant visual sync
        embedded_res = self.embedded.retain(target_bank, content, memory_type, metadata, tags, context)

        cloud_res = None
        if self.cloud_client:
            try:
                cloud_res = self.cloud_client.retain(bank_id=target_bank, content=str(content), metadata=metadata, tags=tags, context=context)
            except Exception as e:
                print(f"[HindsightService] Cloud retain notice: {e}")

        return {
            "success": True,
            "bank_id": target_bank,
            "embedded": embedded_res,
            "cloud_synced": cloud_res is not None
        }

    def recall(self, query, bank_id=None, types=None, max_tokens=2048):
        target_bank = bank_id or self.bank_id

        # Try cloud client first if available
        if self.cloud_client:
            try:
                cloud_resp = self.cloud_client.recall(bank_id=target_bank, query=query, max_tokens=max_tokens)
                if hasattr(cloud_resp, "to_prompt_string") and callable(cloud_resp.to_prompt_string):
                    p_str = cloud_resp.to_prompt_string()
                else:
                    p_str = str(cloud_resp)
                return {
                    "query": query,
                    "bank_id": target_bank,
                    "engine": "hindsight_cloud",
                    "count": len(getattr(cloud_resp, "results", [])),
                    "prompt_string": p_str,
                    "raw": str(cloud_resp)
                }
            except Exception as e:
                print(f"[HindsightService] Cloud recall failed ({e}), falling back to embedded TEMPR engine.")

        # Fallback to embedded TEMPR recall
        res = self.embedded.recall(target_bank, query, types=types, max_tokens=max_tokens)
        res["engine"] = "embedded_tempr"
        return res

    def reflect(self, query, bank_id=None):
        target_bank = bank_id or self.bank_id
        if self.cloud_client:
            try:
                cloud_resp = self.cloud_client.reflect(bank_id=target_bank, query=query)
                return {
                    "query": query,
                    "bank_id": target_bank,
                    "engine": "hindsight_cloud",
                    "synthesis": getattr(cloud_resp, "text", str(cloud_resp))
                }
            except Exception as e:
                print(f"[HindsightService] Cloud reflect failed ({e}), using embedded reflect.")

        res = self.embedded.reflect(target_bank, query)
        res["engine"] = "embedded_reflect"
        return res

    def get_bank(self, bank_id=None):
        target_bank = bank_id or self.bank_id
        return self.embedded.get_bank_summary(target_bank)

    def reset_scenarios(self, bank_id=None):
        target_bank = bank_id or self.bank_id
        return self.embedded.reset_scenarios(target_bank)

    def clear_bank(self, bank_id=None):
        target_bank = bank_id or self.bank_id
        return self.embedded.clear_bank(target_bank)


# Singleton instance for frAIday server
HINDSIGHT = HindsightService()

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    print("Testing HindsightService...")
    status = HINDSIGHT.get_status()
    print("Status:", json.dumps(status, indent=2))
    recall_test = HINDSIGHT.recall("What port does postgres run on?")
    print("Recall Test Results Count:", recall_test.get("count"))
    print("Recall Test Prompt String:\n", recall_test.get("prompt_string"))

