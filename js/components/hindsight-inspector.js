/**
 * frAIday — Vectorize Hindsight Visual Memory Inspector & Bank Explorer
 * 
 * Features:
 * 1. Live Memory Stream (Real-time recall & retain telemetry)
 * 2. 4-Tier Memory Bank Explorer (Mental Models, Observations, World Facts, Experience Facts)
 * 3. Before/After Demo Mode Switcher (Stateless Baseline vs Hindsight Learning)
 * 4. 1-Click Interactive Hackathon Scenarios
 * 5. Autonomous Reflection Playground
 */

export class HindsightInspector {
  constructor(container, options = {}) {
    this.container = container;
    this.apiBase = options.apiBase || '';
    this.onToggleMode = options.onToggleMode || null;
    this.onRunScenario = options.onRunScenario || null;
    
    const storedHindsight = typeof localStorage !== 'undefined' ? localStorage.getItem('fraiday_hindsight_enabled') : null;
    this.isHindsightEnabled = storedHindsight !== null ? storedHindsight === 'true' : true;
    this.activeTierTab = 'all';
    this.bankData = null;
    this.bankStatus = null;
    this.recallStream = [];
    this.reflectionResult = null;
    this.isReflecting = false;

    this.scenarios = [
      {
        id: 'scenario-db-port',
        title: 'Incident INC-104: Database Port & SSL Trap',
        icon: '🐘',
        category: 'DevOps / Database',
        prompt: 'Configure database connection settings for local PostgreSQL service and write a quick connection verification test.',
        statelessOutcome: 'Fails with ConnectionRefusedError: defaults to port 5432 with sslmode=require (ignores repo Docker port mapping).',
        hindsightOutcome: 'Succeeds immediately: recalls Mental Model #1 + INC-104 post-mortem (uses port 5433, sslmode=disable).'
      },
      {
        id: 'scenario-pydantic-v2',
        title: 'Modern Pydantic v2 Migration Standard',
        icon: '⚡',
        category: 'Code Conventions',
        prompt: 'Create user registration data schema and validator with Pydantic for user auth flow.',
        statelessOutcome: 'Uses outdated Pydantic v1 syntax (class Config: orm_mode=True, .dict()) causing deprecation errors.',
        hindsightOutcome: 'Recalls Mental Model #2: writes modern model_config = ConfigDict(from_attributes=True) and .model_dump().'
      },
      {
        id: 'scenario-devops-cors',
        title: 'Workspace Web Server CORS & Health Protocol',
        icon: '🌐',
        category: 'Security / Architecture',
        prompt: 'Write a lightweight Python HTTP server in ./workspace/ with a /users endpoint for frontend consumption.',
        statelessOutcome: 'Omits CORS headers and OPTIONS handler, causing browser iframe preview to block API requests.',
        hindsightOutcome: 'Recalls Mental Model #3: automatically adds Access-Control-Allow-Origin: * and /health probe.'
      }
    ];

    this.init();
  }

  async init() {
    this.render();
    await this.refreshData();
  }

  async refreshData() {
    try {
      const [statusRes, bankRes] = await Promise.all([
        fetch(`${this.apiBase}/api/hindsight/status`).then(r => r.json()).catch(() => null),
        fetch(`${this.apiBase}/api/hindsight/bank`).then(r => r.json()).catch(() => null)
      ]);

      if (statusRes) this.bankStatus = statusRes;
      if (bankRes && bankRes.bank) this.bankData = bankRes.bank;
      this.updateStatsAndTiers();
    } catch (err) {
      console.warn('Failed to refresh Hindsight data:', err);
    }
  }

  handleRecallEvent(recallData) {
    if (!recallData) return;
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const entry = {
      timestamp: now,
      query: recallData.query || 'Contextual Codebase Query',
      count: (recallData.results || []).length,
      results: recallData.results || [],
      disabled: recallData.disabled || false
    };
    this.recallStream.unshift(entry);
    if (this.recallStream.length > 20) this.recallStream.pop();
    this.renderStream();
    this.refreshData();
  }

  handleRetainEvent(retainData) {
    this.refreshData();
  }

  toggleMode(enabled) {
    this.isHindsightEnabled = enabled;
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem('fraiday_hindsight_enabled', this.isHindsightEnabled ? 'true' : 'false');
      } catch (_) {}
    }
    if (this.onToggleMode) {
      this.onToggleMode(this.isHindsightEnabled);
    }
    this.render();
  }

  async triggerReflection() {
    this.isReflecting = true;
    this.render();
    try {
      const res = await fetch(`${this.apiBase}/api/hindsight/reflect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: "Synthesize our repository's core architectural standards, database conventions, and learned incident resolutions."
        })
      }).then(r => r.json());

      this.reflectionResult = res.synthesis || 'No reflection response generated.';
    } catch (err) {
      this.reflectionResult = `Reflection error: ${err.message}`;
    } finally {
      this.isReflecting = false;
      this.render();
    }
  }

  async resetScenarios() {
    if (!confirm('Reset Hindsight memory bank to benchmark hackathon scenarios?')) return;
    try {
      await fetch(`${this.apiBase}/api/hindsight/reset-scenarios`, { method: 'POST' });
      await this.refreshData();
      alert('Hindsight Memory Bank re-seeded with benchmark scenarios!');
    } catch (err) {
      alert(`Reset failed: ${err.message}`);
    }
  }

  render() {
    if (!this.container) return;

    const stats = this.bankStatus?.stats || {
      mental_models: 3,
      observations: 3,
      world_facts: 2,
      experience_facts: 2,
      total: 10
    };

    const isCloud = this.bankStatus?.is_cloud_active || false;
    const engineLabel = isCloud ? 'Hindsight Cloud API' : 'Embedded TEMPR Engine';

    this.container.innerHTML = `
      <div class="hindsight-inspector-root">
        
        <!-- Header Banner -->
        <div class="hs-header">
          <div class="hs-header-left">
            <div class="hs-logo-badge">🧠</div>
            <div>
              <div class="hs-title">
                Vectorize Hindsight Memory
                <span class="hs-engine-pill ${isCloud ? 'cloud' : 'local'}">${engineLabel}</span>
              </div>
              <div class="hs-subtitle">Biomimetic Retain · TEMPR Hybrid Recall · Reflect Synthesis</div>
            </div>
          </div>

          <div class="hs-header-right">
            <!-- Mode Toggle Switch -->
            <div class="hs-mode-switcher ${this.isHindsightEnabled ? 'mode-active' : 'mode-baseline'}" title="Toggle between Hindsight Learning Agent and Stateless Baseline Agent for demo comparison">
              <span class="hs-mode-label">${this.isHindsightEnabled ? '● Hindsight Active' : '○ Stateless Baseline'}</span>
              <button class="hs-toggle-btn" id="hs-btn-toggle-mode">
                ${this.isHindsightEnabled ? 'Switch to Baseline' : 'Enable Hindsight'}
              </button>
            </div>
          </div>
        </div>

        <!-- Mode Advisory Alert -->
        ${!this.isHindsightEnabled ? `
          <div class="hs-banner-stateless">
            <strong>⚠️ STATELESS BASELINE DEMO MODE ACTIVE</strong>: Memory injection is bypassed. The agent operates without memory across sessions (demonstrating how standard AI models repeat past mistakes).
          </div>
        ` : `
          <div class="hs-banner-hindsight">
            <strong>✨ HINDSIGHT LEARNING MODE ACTIVE</strong>: Multi-strategy TEMPR hybrid retrieval is actively injecting past incident post-mortems, verified observations, and codebase mental models before every task.
          </div>
        `}

        <!-- Metrics Grid -->
        <div class="hs-metrics-grid">
          <div class="hs-metric-card" data-tier="mental_models">
            <div class="hs-metric-val">${stats.mental_models}</div>
            <div class="hs-metric-label">Mental Models</div>
            <div class="hs-metric-sub">Governing Directives</div>
          </div>
          <div class="hs-metric-card" data-tier="observations">
            <div class="hs-metric-val">${stats.observations}</div>
            <div class="hs-metric-label">Observations</div>
            <div class="hs-metric-sub">Evidence-backed Facts</div>
          </div>
          <div class="hs-metric-card" data-tier="experience_facts">
            <div class="hs-metric-val">${stats.experience_facts}</div>
            <div class="hs-metric-label">Incidents & Fixes</div>
            <div class="hs-metric-sub">Terminal Post-Mortems</div>
          </div>
          <div class="hs-metric-card" data-tier="world_facts">
            <div class="hs-metric-val">${stats.world_facts}</div>
            <div class="hs-metric-label">World Facts</div>
            <div class="hs-metric-sub">Repo & Tech Stack</div>
          </div>
        </div>

        <!-- Section 1: Interactive Hackathon Scenarios -->
        <div class="hs-section">
          <div class="hs-section-header">
            <div class="hs-section-title">
              <span>🚀</span> 1-Click Hackathon Demo Scenarios
            </div>
            <button class="btn btn-secondary btn-xs" id="hs-btn-reset-scenarios" title="Reset bank to initial benchmark state">
              ↺ Reset Bank
            </button>
          </div>
          <div class="hs-scenarios-grid">
            ${this.scenarios.map(s => `
              <div class="hs-scenario-card" data-id="${s.id}">
                <div class="hs-sc-head">
                  <span class="hs-sc-icon">${s.icon}</span>
                  <div>
                    <div class="hs-sc-title">${s.title}</div>
                    <div class="hs-sc-cat">${s.category}</div>
                  </div>
                </div>
                <div class="hs-sc-prompt">"${s.prompt}"</div>
                <div class="hs-sc-comparison">
                  <div class="hs-sc-comp-item stateless">
                    <span class="tag">Without Memory:</span> ${s.statelessOutcome}
                  </div>
                  <div class="hs-sc-comp-item hindsight">
                    <span class="tag">With Hindsight:</span> ${s.hindsightOutcome}
                  </div>
                </div>
                <button class="btn btn-primary btn-sm hs-btn-run-sc" data-id="${s.id}">
                  ▶ Load Objective into frAIday
                </button>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Section 2: Live Memory Stream -->
        <div class="hs-section">
          <div class="hs-section-header">
            <div class="hs-section-title">
              <span>📡</span> Live Memory Telemetry Stream
            </div>
            <span style="font-size:11px;color:var(--text-muted);">Real-time recall pulses during execution</span>
          </div>
          <div id="hs-recall-stream-container">
            ${this.renderStreamHtml()}
          </div>
        </div>

        <!-- Section 3: 4-Tier Memory Bank Explorer -->
        <div class="hs-section">
          <div class="hs-section-header">
            <div class="hs-section-title">
              <span>🗄️</span> 4-Tier Memory Bank Explorer
            </div>
            <div class="hs-tier-tabs">
              <button class="hs-tab-btn ${this.activeTierTab === 'all' ? 'active' : ''}" data-tab="all">All (${stats.total})</button>
              <button class="hs-tab-btn ${this.activeTierTab === 'mental_models' ? 'active' : ''}" data-tab="mental_models">Mental Models</button>
              <button class="hs-tab-btn ${this.activeTierTab === 'observations' ? 'active' : ''}" data-tab="observations">Observations</button>
              <button class="hs-tab-btn ${this.activeTierTab === 'experience_facts' ? 'active' : ''}" data-tab="experience_facts">Incidents</button>
              <button class="hs-tab-btn ${this.activeTierTab === 'world_facts' ? 'active' : ''}" data-tab="world_facts">World Facts</button>
            </div>
          </div>
          <div id="hs-tier-cards-container">
            ${this.renderTierCardsHtml()}
          </div>
        </div>

        <!-- Section 4: Reflection Playground -->
        <div class="hs-section" style="margin-bottom:24px;">
          <div class="hs-section-header">
            <div class="hs-section-title">
              <span>✨</span> Hindsight Reflection Synthesis
            </div>
            <button class="btn btn-primary btn-sm" id="hs-btn-reflect" ${this.isReflecting ? 'disabled' : ''}>
              ${this.isReflecting ? '⚡ Synthesizing...' : '🧠 Trigger Hindsight Reflect'}
            </button>
          </div>
          <div class="hs-reflect-card">
            ${this.isReflecting ? `
              <div style="padding:24px;text-align:center;color:#38bdf8;">
                <div style="display:inline-block;animation:spin 1s linear infinite;font-size:24px;">⚙️</div>
                <div style="margin-top:8px;font-size:12px;">Synthesizing evidence-backed mental models & incident post-mortems...</div>
              </div>
            ` : this.reflectionResult ? `
              <div class="hs-reflect-content">
                ${this.formatMarkdown(this.reflectionResult)}
              </div>
            ` : `
              <div style="color:var(--text-muted);font-size:12px;line-height:1.6;">
                Click <strong>Trigger Hindsight Reflect</strong> above to invoke Hindsight's autonomous reasoning engine across all accumulated memories, producing a consolidated playbook of codebase rules and incident resolutions.
              </div>
            `}
          </div>
        </div>

      </div>
    `;

    this.bindEvents();
  }

  renderStreamHtml() {
    if (!this.recallStream || this.recallStream.length === 0) {
      return `
        <div class="hs-empty-stream">
          <span>💤</span> No live recalls executed yet. Run any mission or click a demo scenario above to view real-time Hindsight TEMPR retrieval pulses.
        </div>
      `;
    }

    return `
      <div class="hs-stream-list">
        ${this.recallStream.map((item, idx) => `
          <div class="hs-stream-card ${item.disabled ? 'disabled' : ''}">
            <div class="hs-stream-header">
              <span class="hs-stream-time">${item.timestamp}</span>
              <span class="hs-stream-q">Query: "${item.query}"</span>
              <span class="badge ${item.disabled ? 'badge-warn' : 'badge-success'}">
                ${item.disabled ? 'Bypassed (Stateless)' : `Recalled ${item.count} items`}
              </span>
            </div>
            ${item.results && item.results.length > 0 ? `
              <div class="hs-stream-results">
                ${item.results.map(r => `
                  <div class="hs-stream-item">
                    <span class="tier-pill ${r.tier}">${r.tier.replace('_', ' ')}</span>
                    <span class="score-pill">score: ${r.score}</span>
                    <span class="text">${r.text}</span>
                  </div>
                `).join('')}
              </div>
            ` : ''}
          </div>
        `).join('')}
      </div>
    `;
  }

  renderStream() {
    const el = this.container?.querySelector('#hs-recall-stream-container');
    if (el) {
      el.innerHTML = this.renderStreamHtml();
    }
  }

  renderTierCardsHtml() {
    if (!this.bankData) {
      return `<div style="padding:20px;text-align:center;color:var(--text-muted);">Loading memory bank...</div>`;
    }

    const cards = [];

    // Mental models
    if (this.activeTierTab === 'all' || this.activeTierTab === 'mental_models') {
      (this.bankData.mental_models || []).forEach(mm => {
        cards.push(`
          <div class="hs-bank-card tier-mental-model">
            <div class="card-head">
              <span class="tier-tag mental-model">MENTAL MODEL</span>
              <span class="card-title">${mm.title}</span>
              <span class="card-conf">conf: ${(mm.confidence * 100).toFixed(0)}%</span>
            </div>
            <div class="card-body">${mm.directive}</div>
            <div class="card-footer">
              <span class="tags">${(mm.applies_to || []).map(t => `#${t}`).join(' ')}</span>
              <span class="time">${new Date(mm.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        `);
      });
    }

    // Observations
    if (this.activeTierTab === 'all' || this.activeTierTab === 'observations') {
      (this.bankData.observations || []).forEach(obs => {
        cards.push(`
          <div class="hs-bank-card tier-observation">
            <div class="card-head">
              <span class="tier-tag observation">OBSERVATION</span>
              <span class="card-proofs">✓ ${obs.proof_count} Proofs</span>
            </div>
            <div class="card-body">${obs.fact}</div>
            ${obs.quotes && obs.quotes.length > 0 ? `
              <div class="card-quotes">
                ${obs.quotes.map(q => `<div class="quote-line">“${q}”</div>`).join('')}
              </div>
            ` : ''}
            <div class="card-footer">
              <span class="tags">${(obs.tags || []).map(t => `#${t}`).join(' ')}</span>
              <span class="time">${new Date(obs.last_verified).toLocaleDateString()}</span>
            </div>
          </div>
        `);
      });
    }

    // Experience facts (Incidents)
    if (this.activeTierTab === 'all' || this.activeTierTab === 'experience_facts') {
      (this.bankData.experience_facts || []).forEach(exp => {
        cards.push(`
          <div class="hs-bank-card tier-incident">
            <div class="card-head">
              <span class="tier-tag incident">POST-MORTEM [${exp.incident_id || 'INC'}]</span>
              <span class="card-title">${exp.title}</span>
            </div>
            <div class="card-body">
              <p><strong>Root Cause:</strong> ${exp.root_cause}</p>
              <p style="margin-top:6px;color:#10b981;"><strong>Verified Resolution:</strong> ${exp.resolution}</p>
            </div>
            <div class="card-footer">
              <span class="tags">${(exp.tags || []).map(t => `#${t}`).join(' ')}</span>
              <span class="status-badge resolved">Resolved</span>
            </div>
          </div>
        `);
      });
    }

    // World facts
    if (this.activeTierTab === 'all' || this.activeTierTab === 'world_facts') {
      (this.bankData.world_facts || []).forEach(wf => {
        cards.push(`
          <div class="hs-bank-card tier-world-fact">
            <div class="card-head">
              <span class="tier-tag world-fact">WORLD FACT</span>
              <span class="card-src">source: ${wf.source || 'workspace'}</span>
            </div>
            <div class="card-body">${wf.fact}</div>
            <div class="card-footer">
              <span class="tags">${(wf.tags || []).map(t => `#${t}`).join(' ')}</span>
            </div>
          </div>
        `);
      });
    }

    if (cards.length === 0) {
      return `<div style="padding:24px;text-align:center;color:var(--text-muted);">No memories found in this tier.</div>`;
    }

    return `<div class="hs-cards-grid">${cards.join('')}</div>`;
  }

  updateStatsAndTiers() {
    const el = this.container?.querySelector('#hs-tier-cards-container');
    if (el) {
      el.innerHTML = this.renderTierCardsHtml();
    }
  }

  bindEvents() {
    if (!this.container) return;

    // Mode Toggle
    const btnToggle = this.container.querySelector('#hs-btn-toggle-mode');
    if (btnToggle) {
      btnToggle.addEventListener('click', () => {
        this.toggleMode(!this.isHindsightEnabled);
      });
    }

    // Scenario Launchers
    this.container.querySelectorAll('.hs-btn-run-sc').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const scId = e.currentTarget.getAttribute('data-id');
        const scenario = this.scenarios.find(s => s.id === scId);
        if (scenario && this.onRunScenario) {
          this.onRunScenario(scenario.prompt, this.isHindsightEnabled);
        }
      });
    });

    // Reset Scenarios
    const btnReset = this.container.querySelector('#hs-btn-reset-scenarios');
    if (btnReset) {
      btnReset.addEventListener('click', () => this.resetScenarios());
    }

    // Trigger Reflection
    const btnReflect = this.container.querySelector('#hs-btn-reflect');
    if (btnReflect) {
      btnReflect.addEventListener('click', () => this.triggerReflection());
    }

    // Tier Tabs
    this.container.querySelectorAll('.hs-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.container.querySelectorAll('.hs-tab-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.activeTierTab = e.currentTarget.getAttribute('data-tab');
        this.updateStatsAndTiers();
      });
    });
  }

  formatMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/^### (.*$)/gim, '<h3 style="color:#38bdf8;font-size:14px;margin:12px 0 6px;">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 style="color:#e2e8f0;font-size:15px;margin:14px 0 6px;">$1</h2>')
      .replace(/\*\*(.*?)\*\*/gim, '<strong style="color:#f8fafc;">$1</strong>')
      .replace(/^\- (.*$)/gim, '<li style="margin-left:16px;color:#cbd5e1;font-size:12.5px;margin-bottom:4px;">$1</li>')
      .replace(/\n\n/gim, '<br/>');
  }
}
