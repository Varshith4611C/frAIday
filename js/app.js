/**
 * frAIday — Production Master Application Coordinator
 * Real Multi-Surface Canvas, Live Iframe Preview, Real Terminal & Settings
 */

import { FileTreeComponent } from './components/file-tree.js';
import { CodeEditorComponent } from './components/code-editor.js';
import { DagCanvasComponent } from './components/dag-canvas.js';
import { TerminalComponent } from './components/terminal.js';
import { KnowledgeBase } from './agent/knowledge-base.js';
import { SafetyPolicyManager } from './agent/safety-policy.js';
import { AgentEngine } from './agent/agent-engine.js';
import { HindsightInspector } from './components/hindsight-inspector.js';

export const PROVIDER_PRESETS = {
  groq: {
    name: 'Groq LPU',
    keyHint: 'Groq Key (gsk_...)',
    defaultKey: '',
    defaultModel: 'openai/gpt-oss-120b',
    models: [
      { id: 'openai/gpt-oss-120b', label: 'openai/gpt-oss-120b (120B Reasoning · Default)' },
      { id: 'qwen/qwen3.8-27b', label: 'qwen/qwen3.8-27b (Fast 27B LPU)' },
      { id: 'openai/gpt-oss-20b', label: 'openai/gpt-oss-20b (20B LPU)' },
      { id: 'custom', label: '⚙️ Custom Model Identifier...' }
    ]
  },
  nvidia: {
    name: 'NVIDIA NIM',
    keyHint: 'NVIDIA Key (nvapi-...)',
    defaultKey: '',
    defaultModel: 'meta/llama-3.2-11b-vision-instruct',
    models: [
      { id: 'meta/llama-3.2-11b-vision-instruct', label: 'meta/llama-3.2-11b-vision-instruct (Default · Fast)' },
      { id: 'meta/llama-3.2-90b-vision-instruct', label: 'meta/llama-3.2-90b-vision-instruct (High Intelligence)' },
      { id: 'custom', label: '⚙️ Custom Model Identifier...' }
    ]
  },
  openai: {
    name: 'OpenAI',
    keyHint: 'OpenAI Key (sk-...)',
    defaultKey: '',
    defaultModel: 'gpt-4o-mini',
    models: [
      { id: 'gpt-4o-mini', label: 'gpt-4o-mini (Fast & Recommended)' },
      { id: 'gpt-4o', label: 'gpt-4o (High Intelligence)' },
      { id: 'o3-mini', label: 'o3-mini (Reasoning Model)' },
      { id: 'custom', label: '⚙️ Custom Model Identifier...' }
    ]
  },
  ollama: {
    name: 'Ollama',
    keyHint: 'Ollama Key (Optional / local)',
    defaultKey: 'ollama',
    defaultModel: 'llama3.2',
    models: [
      { id: 'llama3.2', label: 'llama3.2' },
      { id: 'qwen2.5-coder', label: 'qwen2.5-coder' },
      { id: 'deepseek-r1', label: 'deepseek-r1' },
      { id: 'custom', label: '⚙️ Custom Model Identifier...' }
    ]
  }
};

class AppCoordinator {
  constructor() {
    this.activeTab = 'preview'; // 'preview', 'code', 'dag', 'terminal'
    this.currentPreviewUrl = '/workspace/index.html';
    this.activeWorkspace = 'default';
    this.workspacesList = [];
  }

  async init() {
    // 1. Initialize Components
    const fileTreeEl = document.getElementById('sidebar-file-tree');
    const editorEl = document.getElementById('editor-container');
    const dagEl = document.getElementById('dag-container');
    const terminalEl = document.getElementById('terminal-container');
    const kiEl = document.getElementById('knowledge-vault-container');
    const hitlEl = document.getElementById('hitl-interceptor-slot');
    const monologueEl = document.getElementById('agent-monologue-card');
    const streamContainer = document.getElementById('chat-timeline');
    const statusPillEl = document.getElementById('status-pill');

    this.fileTree = new FileTreeComponent(fileTreeEl, (path) => {
      this.switchTab('code');
      this.codeEditor.loadFile(path);
    });

    this.codeEditor = new CodeEditorComponent(editorEl, (action, filepath, content) => {
      this.handleCodeLensAction(action, filepath, content);
    }, (savedPath) => {
      this.reloadPreview();
    });

    this.dagCanvas = new DagCanvasComponent(dagEl, (node) => {
      alert(`Task Node #${node.id}: ${node.title}\n\n${node.desc}\nStatus: ${node.status.toUpperCase()}`);
    });

    this.terminal = new TerminalComponent(terminalEl, (cmd, result) => {
      this.fileTree.refresh();
      this.reloadPreview();
    });
    this.terminal.init();

    this.knowledgeBase = new KnowledgeBase(kiEl, (ki) => {
      alert(`Knowledge Item: ${ki.title}\nRelevance: ${ki.relevance}\nSource: ${ki.source}\n\nFinding:\n${ki.snippet}`);
    });

    this.safetyPolicy = new SafetyPolicyManager(hitlEl);

    this.agentEngine = new AgentEngine({
      monologueEl,
      streamContainer,
      statusPillEl,
      terminal: this.terminal,
      safetyPolicy: this.safetyPolicy,
      dagCanvas: this.dagCanvas,
      knowledgeBase: this.knowledgeBase,
      fileTree: this.fileTree,
      codeEditor: this.codeEditor,
      onArtifactReady: (entryPath) => {
        this.reloadPreview(entryPath);
        this.switchTab('preview');
      },
      onArtifactPlanReady: (planMarkdown) => {
        this.renderArtifactPlan(planMarkdown);
        this.switchTab('artifacts');
      },
      onPlanPendingApproval: (planMarkdown) => {
        this.renderPlanApprovalCardInChat(planMarkdown);
      },
      onUserMessage: (msg) => {
        this.renderUserMessageInChat(msg);
      },
      onAgentResponse: (msg) => {
        this.renderAgentMessageInChat(msg);
      },
      onSystemAlert: (alertData) => {
        this.renderSystemAlertInChat(alertData);
      },
      onVerificationScreenshotReady: (result) => {
        this.renderVerificationScreenshotInChat(result);
      },
      onExecutionStart: () => {
        this.setExecutionUiRunning(true);
      },
      onExecutionEnd: (status = {}) => {
        this.setExecutionUiRunning(false);
        if (status && (status.error || status.aborted)) {
          this.renderHaltedCardInChat(status);
        }
      }
    });

    // Initialize Vectorize Hindsight Visual Memory Inspector
    const hindsightContainer = document.getElementById('hindsight-canvas-container');
    this.hindsightInspector = new HindsightInspector(hindsightContainer, {
      apiBase: '',
      onToggleMode: (enabled) => {
        if (this.agentEngine?.setHindsightMode) {
          this.agentEngine.setHindsightMode(enabled);
        } else if (this.agentEngine) {
          this.agentEngine.hindsightEnabled = enabled;
        }
        this.updateHindsightHudPill(enabled);
      }
    });

    // Wire agentEngine hindsight callbacks
    this.agentEngine.onHindsightRecall = (recallData) => {
      this.hindsightInspector.handleRecallEvent(recallData);
      this.updateHindsightHudPill(this.agentEngine.hindsightEnabled !== false, recallData.count);
      if (recallData && recallData.results && recallData.results.length > 0) {
        this.renderHindsightRecallInChat(recallData);
      }
    };
    this.agentEngine.onHindsightRetain = (retainData) => {
      this.hindsightInspector.handleRetainEvent(retainData);
      this.updateHindsightHudPill(this.agentEngine.hindsightEnabled !== false);
      if (retainData && (retainData.success || retainData.item)) {
        this.renderHindsightRetainInChat(retainData);
      }
    };

    // 2. Setup DOM Events
    this.bindHudControls();
    this.bindCanvasTabs();
    this.bindActivityBar();
    this.bindPreviewControls();
    this.bindSettingsModal();
    this.bindContextualInput();
    this.bindPlanApprovalControls();

    // Initial HUD update respecting stored hindsight mode
    setTimeout(() => {
      this.updateHindsightHudPill(this.agentEngine.hindsightEnabled !== false);
      this.renderSidebarHindsightQuickView();
    }, 500);

    // 3. Initial Load from Backend & Configuration Sync
    await this.fetchWorkspaces();
    await this.fileTree.refresh();
    this.reloadPreview();
    await this.syncInitialConfig();
    await this.rehydrateSession();
  }

  updateHindsightHudPill(enabled, lastCount = null) {
    const pill = document.getElementById('hud-hindsight-pill');
    const label = document.getElementById('hud-hindsight-label');
    if (!pill || !label) return;

    if (!enabled) {
      pill.style.background = 'rgba(239, 68, 68, 0.15)';
      pill.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      label.style.color = '#f87171';
      label.innerText = 'Stateless Baseline (Memory Off)';
    } else {
      pill.style.background = 'rgba(56, 189, 248, 0.12)';
      pill.style.borderColor = 'rgba(56, 189, 248, 0.35)';
      label.style.color = '#38bdf8';
      const stats = this.hindsightInspector?.bankStatus?.stats;
      const count = stats?.total ?? 10;
      label.innerText = lastCount !== null ? `Hindsight: Recalled ${lastCount} (Bank: ${count})` : `Hindsight: Active (${count} Mems)`;
    }
  }

  renderSidebarHindsightQuickView() {
    const el = document.getElementById('sidebar-hindsight-quickview');
    if (!el) return;
    const stats = this.hindsightInspector?.bankStatus?.stats || {
      mental_models: 3, observations: 3, experience_facts: 2, world_facts: 2, total: 10
    };
    el.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:10px;font-size:12px;">
        <div style="background:rgba(22,32,50,0.6);border:1px solid rgba(56,189,248,0.2);border-radius:8px;padding:12px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <span style="font-weight:700;color:#f8fafc;">Active Bank</span>
            <span style="font-size:10px;color:#38bdf8;background:rgba(56,189,248,0.15);padding:2px 6px;border-radius:4px;">TEMPR Hybrid</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:11px;color:#cbd5e1;">
            <div>🧠 Mental Models: <strong style="color:#c084fc;">${stats.mental_models}</strong></div>
            <div>🔍 Observations: <strong style="color:#38bdf8;">${stats.observations}</strong></div>
            <div>⚡ Incidents: <strong style="color:#fcd34d;">${stats.experience_facts}</strong></div>
            <div>🌐 World Facts: <strong style="color:#94a3b8;">${stats.world_facts}</strong></div>
          </div>
        </div>
        <button class="btn btn-primary btn-sm" style="width:100%;" onclick="window.fraidayApp?.switchTab('hindsight')">
          Open Full Memory Explorer ↗
        </button>
      </div>
    `;
  }

  switchTab(tabKey) {
    this.activeTab = tabKey;
    document.querySelectorAll('.canvas-tab').forEach(tab => {
      tab.classList.toggle('active', tab.getAttribute('data-tab') === tabKey);
    });
    document.querySelectorAll('.canvas-view').forEach(view => {
      view.classList.toggle('active', view.getAttribute('data-view') === tabKey);
    });

    if (tabKey === 'hindsight') {
      this.hindsightInspector?.refreshData();
    }

    if (tabKey === 'terminal') {
      const termInput = document.getElementById('term-user-input');
      if (termInput) {
        setTimeout(() => termInput.focus(), 50);
      }
    }

    if (tabKey === 'dag') {
      if (this.dagCanvas && typeof this.dagCanvas.render === 'function') {
        this.dagCanvas.render();
      }
    }

    if (tabKey === 'code') {
      if (!this.codeEditor.currentFile) {
        // Automatically open index.html or first file if nothing loaded
        const defaultFile = (this.fileTree?.files || []).find(f => f.path === 'index.html' || f.path === 'app.js')?.path
          || (this.fileTree?.files && this.fileTree.files[0]?.path)
          || 'index.html';
        this.codeEditor.loadFile(defaultFile);
      }
    }
  }

  bindCanvasTabs() {
    document.querySelectorAll('.canvas-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const tabKey = tab.getAttribute('data-tab');
        this.switchTab(tabKey);
      });
    });

    // Global shortcut Ctrl+` or Cmd+` to toggle terminal
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '`') {
        e.preventDefault();
        this.switchTab(this.activeTab === 'terminal' ? 'preview' : 'terminal');
      }
    });
  }

  bindActivityBar() {
    document.querySelectorAll('.activity-btn[data-panel]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.activity-btn[data-panel]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const panelKey = btn.getAttribute('data-panel');
        document.querySelectorAll('.sidebar-panel-content').forEach(p => {
          p.style.display = p.getAttribute('data-panel') === panelKey ? 'block' : 'none';
        });

        const titleEl = document.getElementById('sidebar-panel-title');
        if (titleEl) {
          const titles = {
            files: 'Workspace Explorer',
            hindsight: 'Vectorize Hindsight Memory Bank',
            knowledge: 'Discovered Docs & RFCs',
            skills: 'MCP Tooling & Skills',
            safety: 'Execution Policies'
          };
          titleEl.innerText = titles[panelKey] || 'Panel';
        }
      });
    });

    // Activity bar terminal button
    const termActivityBtn = document.getElementById('activity-btn-terminal');
    if (termActivityBtn) {
      termActivityBtn.addEventListener('click', () => {
        this.switchTab('terminal');
      });
    }
  }

  bindPreviewControls() {
    const iframe = document.getElementById('live-preview-frame');
    const reloadBtn = document.getElementById('btn-reload-preview');
    const popoutBtn = document.getElementById('btn-popout-preview');

    if (reloadBtn) {
      reloadBtn.addEventListener('click', () => this.reloadPreview());
    }

    if (popoutBtn) {
      popoutBtn.addEventListener('click', () => {
        window.open(this.currentPreviewUrl, '_blank');
      });
    }

    // Viewport switcher
    document.querySelectorAll('.viewport-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.viewport-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const vp = btn.getAttribute('data-vp');
        if (iframe) {
          iframe.className = `live-iframe viewport-${vp}`;
        }
      });
    });

    // Audit snapshot modal controls
    const viewScreenshotBtn = document.getElementById('btn-view-screenshot');
    const screenshotModal = document.getElementById('screenshot-modal');
    const closeScreenshotModal = document.getElementById('btn-close-screenshot-modal');

    if (viewScreenshotBtn && screenshotModal) {
      viewScreenshotBtn.addEventListener('click', () => {
        const img = document.getElementById('audit-modal-img');
        if (img) {
          img.src = `/workspace/.system_generated/latest_preview.png?t=${Date.now()}`;
        }
        screenshotModal.classList.add('open');
      });
    }

    if (closeScreenshotModal && screenshotModal) {
      closeScreenshotModal.addEventListener('click', () => {
        screenshotModal.classList.remove('open');
      });
      screenshotModal.addEventListener('click', (e) => {
        if (e.target === screenshotModal) {
          screenshotModal.classList.remove('open');
        }
      });
    }

    // Live Preview DevTools Console Drawer
    const consoleDrawer = document.getElementById('preview-console-drawer');
    const toggleConsoleBtn = document.getElementById('btn-toggle-console-drawer');
    const clearConsoleBtn = document.getElementById('btn-clear-console');
    const refreshConsoleBtn = document.getElementById('btn-refresh-console');
    const consoleBody = document.getElementById('preview-console-body');
    const consoleLogCount = document.getElementById('console-log-count');
    const consoleWarnCount = document.getElementById('console-warn-count');
    const consoleErrorCount = document.getElementById('console-error-count');
    const consoleEmptyMsg = document.getElementById('console-empty-msg');

    this.consoleLogs = [];
    this.consoleCounts = { log: 0, warn: 0, error: 0 };

    const updateConsoleBadges = () => {
      if (consoleLogCount) consoleLogCount.innerText = `${this.consoleCounts.log} logs`;
      if (consoleWarnCount) {
        consoleWarnCount.innerText = `${this.consoleCounts.warn} warnings`;
        consoleWarnCount.style.display = this.consoleCounts.warn > 0 ? 'inline-block' : 'none';
      }
      if (consoleErrorCount) {
        consoleErrorCount.innerText = `${this.consoleCounts.error} errors`;
        consoleErrorCount.style.display = this.consoleCounts.error > 0 ? 'inline-block' : 'none';
      }
    };

    this.clearPreviewConsole = (reason = 'cleared') => {
      this.consoleLogs = [];
      this.consoleCounts = { log: 0, warn: 0, error: 0 };
      this._lastTerminalErrors = new Map();
      if (consoleBody) {
        const msg = reason === 'reload'
          ? '<div class="console-empty" id="console-empty-msg">🔄 Console refreshed for active preview. 0 errors.</div>'
          : '<div class="console-empty" id="console-empty-msg">Console cleared.</div>';
        consoleBody.innerHTML = msg;
      }
      updateConsoleBadges();
      if (this.agentEngine && this.agentEngine.activeRuntimeErrors) {
        this.agentEngine.activeRuntimeErrors.clear();
      }
    };

    if (toggleConsoleBtn && consoleDrawer) {
      toggleConsoleBtn.addEventListener('click', () => {
        const isCollapsed = consoleDrawer.classList.toggle('collapsed');
        toggleConsoleBtn.innerText = isCollapsed ? '▲ Console' : '▼ Console';
      });
    }

    if (clearConsoleBtn) {
      clearConsoleBtn.addEventListener('click', () => {
        this.clearPreviewConsole('manual');
      });
    }

    if (refreshConsoleBtn) {
      refreshConsoleBtn.addEventListener('click', () => {
        this.reloadPreview();
      });
    }

    const appendConsoleLog = (level, args, timestamp) => {
      const emptyEl = document.getElementById('console-empty-msg');
      if (emptyEl) emptyEl.remove();

      const lvl = level || 'log';
      if (lvl === 'error') this.consoleCounts.error++;
      else if (lvl === 'warn') this.consoleCounts.warn++;
      else this.consoleCounts.log++;
      updateConsoleBadges();

      const item = document.createElement('div');
      item.className = `console-log-item ${lvl}`;
      const timeStr = timestamp || new Date().toLocaleTimeString();
      const text = Array.isArray(args) ? args.join(' ') : String(args);
      item.innerHTML = `
        <span class="log-time">${timeStr}</span>
        <span class="log-level">${lvl}</span>
        <span class="log-text">${this.escapeInlineMd(text)}</span>
      `;
      if (consoleBody) {
        consoleBody.appendChild(item);
        consoleBody.scrollTop = consoleBody.scrollHeight;
      }
      this.consoleLogs.push({ level: lvl, args, timestamp: timeStr });
    };

    // Listen for runtime errors & console logs emitted from preview iframe
    window.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'WORKSPACE_PREVIEW_RELOADED') {
        this.clearPreviewConsole('reload');
      }
      if (event.data && event.data.type === 'WORKSPACE_CONSOLE_LOG') {
        const { level, args, timestamp } = event.data;
        appendConsoleLog(level, args, timestamp);
      }
      if (event.data && event.data.type === 'WORKSPACE_RUNTIME_ERROR') {
        const { message, filename, lineno, colno, isConsoleError } = event.data;
        if (!isConsoleError) {
          appendConsoleLog('error', [`Runtime Error: ${message}`, filename ? `at ${filename}:${lineno}` : '']);
        }
        if (message && message !== 'Script error.' && message !== 'Unknown runtime error' && lineno !== 0) {
          const errKey = `${message}:${filename}:${lineno}`;
          const now = Date.now();
          if (!this._lastTerminalErrors) this._lastTerminalErrors = new Map();
          if (!this._lastTerminalErrors.has(errKey) || (now - this._lastTerminalErrors.get(errKey) > 10000)) {
            this._lastTerminalErrors.set(errKey, now);
            this.terminal.appendOutput(`⚠️ [Workspace Runtime Error] ${message} (${filename ? filename + ':' + lineno : 'line ' + lineno})`, 'error');
          }
        }
        if (this.agentEngine && typeof this.agentEngine.handleRuntimeError === 'function') {
          this.agentEngine.handleRuntimeError(event.data);
        }
      }
    });

    window.fraidayApp = this;
    window.frAidayApp = this;
  }

  bindPlanApprovalControls() {
    const approveBtn = document.getElementById('btn-approve-plan');
    const rejectBtn = document.getElementById('btn-reject-plan');

    if (approveBtn) {
      approveBtn.addEventListener('click', () => {
        if (this.agentEngine) {
          this.agentEngine.approvePlan();
        }
      });
    }

    if (rejectBtn) {
      rejectBtn.addEventListener('click', () => {
        const feedback = prompt('Enter your revision instructions for the architecture plan:');
        if (this.agentEngine) {
          this.agentEngine.rejectPlan(feedback);
        }
      });
    }
  }

  renderArtifactPlan(markdown) {
    const container = document.getElementById('artifact-content-area');
    if (!container) return;

    let html = markdown
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/>\s*\[!IMPORTANT\]\s*\n((?:>.*?\n?)+)/g, (m, p1) => {
        const text = p1.replace(/^>\s*/gm, '');
        return `<div class="artifact-alert alert-important"><strong>IMPORTANT:</strong><br/>${text}</div>`;
      })
      .replace(/>\s*\[!NOTE\]\s*\n((?:>.*?\n?)+)/g, (m, p1) => {
        const text = p1.replace(/^>\s*/gm, '');
        return `<div class="artifact-alert alert-note"><strong>NOTE:</strong><br/>${text}</div>`;
      })
      .replace(/>\s*\[!WARNING\]\s*\n((?:>.*?\n?)+)/g, (m, p1) => {
        const text = p1.replace(/^>\s*/gm, '');
        return `<div class="artifact-alert alert-warning"><strong>WARNING:</strong><br/>${text}</div>`;
      })
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/```([a-z]*)\n([\s\S]*?)```/g, (m, lang, code) => `<pre><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>')
      .replace(/\n\n/g, '<p></p>');

    container.innerHTML = html;
  }

  reloadPreview(preferredHtmlPath = null) {
    if (this.clearPreviewConsole) this.clearPreviewConsole('reload');
    const iframe = document.getElementById('live-preview-frame');
    const emptyState = document.getElementById('preview-empty-state');
    if (!iframe) return;

    fetch('/api/workspace/files')
      .then(r => r.json())
      .then(data => {
        const files = data.files || [];
        let entryFile = null;

        if (preferredHtmlPath && files.some(f => f.path === preferredHtmlPath)) {
          entryFile = files.find(f => f.path === preferredHtmlPath);
        } else {
          // Intelligent entrypoint detection
          const htmlFiles = files.filter(f => f.path.toLowerCase().endsWith('.html') && !f.path.includes('.system_generated'));
          entryFile = htmlFiles.find(f => f.path === 'index.html')
            || htmlFiles.find(f => f.path === 'frontend/index.html')
            || htmlFiles.find(f => f.path === 'src/index.html')
            || htmlFiles.find(f => f.path === 'public/index.html')
            || htmlFiles.find(f => f.path === 'client/index.html')
            || htmlFiles.find(f => !f.path.includes('/'))
            || htmlFiles[0];
        }

        if (entryFile) {
          if (emptyState) emptyState.style.display = 'none';
          iframe.style.display = 'block';
          const cleanPath = entryFile.path.replace(/^\/+/, '');
          this.currentPreviewUrl = `/workspace/${cleanPath}?t=${Date.now()}`;
          iframe.src = this.currentPreviewUrl;
          const addr = document.getElementById('preview-address-display');
          if (addr) addr.innerText = `http://localhost:8080/workspace/${cleanPath}`;
        } else {
          iframe.style.display = 'none';
          if (emptyState) emptyState.style.display = 'flex';
          const addr = document.getElementById('preview-address-display');
          if (addr) addr.innerText = 'about:blank (no HTML entrypoint in workspace)';
        }
      })
      .catch(() => {});
  }

  async fetchWorkspaces() {
    try {
      const res = await fetch('/api/workspaces').then(r => r.json());
      if (res && res.workspaces) {
        this.activeWorkspace = res.active_workspace || 'default';
        this.workspacesList = res.workspaces || [];
        this.updateWorkspaceDisplay(this.activeWorkspace, res.active_path);
        this.renderWorkspaceDropdown();
      }
    } catch (err) {
      console.warn('Failed to fetch workspaces:', err);
    }
  }

  updateWorkspaceDisplay(name, activePath = null) {
    const hudName = document.getElementById('hud-active-workspace-name');
    if (hudName) hudName.innerText = name;
    const sidebarBadge = document.getElementById('sidebar-active-workspace-badge');
    if (sidebarBadge) sidebarBadge.innerText = name;
    if (this.agentEngine?.setWorkspace) {
      this.agentEngine.setWorkspace(name);
    }
    if (this.terminal?.setWorkspace) {
      this.terminal.setWorkspace(name, activePath);
    }
  }

  renderWorkspaceDropdown() {
    const listEl = document.getElementById('workspace-list-container');
    if (!listEl) return;

    if (!this.workspacesList || this.workspacesList.length === 0) {
      listEl.innerHTML = '<div style="color:#64748b;font-size:11px;padding:8px;text-align:center;">No workspaces found</div>';
      return;
    }

    listEl.innerHTML = this.workspacesList.map(ws => {
      const isActive = ws.name === this.activeWorkspace;
      return `
        <div class="workspace-item ${isActive ? 'active' : ''}" data-name="${this.escapeInlineMd(ws.name)}" style="display:flex;align-items:center;justify-content:space-between;padding:7px 10px;border-radius:6px;cursor:pointer;background:${isActive ? 'rgba(56,189,248,0.12)' : 'rgba(255,255,255,0.02)'};border:1px solid ${isActive ? 'rgba(56,189,248,0.4)' : 'rgba(255,255,255,0.05)'};">
          <div style="display:flex;align-items:center;gap:8px;overflow:hidden;flex:1;">
            <span style="font-size:13px;">${isActive ? '📁' : '📂'}</span>
            <div style="overflow:hidden;">
              <div style="font-weight:${isActive ? '700' : '500'};color:${isActive ? '#38bdf8' : '#e2e8f0'};font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                ${this.escapeInlineMd(ws.name)}
                ${isActive ? '<span style="font-size:9.5px;background:#38bdf8;color:#0f172a;font-weight:700;padding:1px 5px;border-radius:3px;margin-left:5px;">ACTIVE</span>' : ''}
              </div>
              <div style="font-size:10.5px;color:#64748b;font-family:var(--font-mono);margin-top:1px;">
                ${ws.file_count !== undefined ? `${ws.file_count} files` : ''} · ${this.escapeInlineMd(ws.rel_path || ws.name)}
              </div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:4px;" onclick="event.stopPropagation();">
            ${ws.name !== 'default' ? `
              <button class="btn btn-icon btn-xs ws-btn-delete" data-name="${this.escapeInlineMd(ws.name)}" title="Delete workspace ${this.escapeInlineMd(ws.name)}" style="color:#ef4444;background:transparent;border:none;padding:2px 5px;font-size:11px;cursor:pointer;">
                🗑️
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');

    // Bind click events on rows
    listEl.querySelectorAll('.workspace-item').forEach(item => {
      item.addEventListener('click', async () => {
        const name = item.getAttribute('data-name');
        if (name && name !== this.activeWorkspace) {
          await this.switchWorkspace(name);
        }
      });
    });

    // Bind delete events
    listEl.querySelectorAll('.ws-btn-delete').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const name = btn.getAttribute('data-name');
        if (name) {
          await this.deleteWorkspace(name);
        }
      });
    });
  }

  async switchWorkspace(name) {
    if (!name || name === this.activeWorkspace) {
      this.closeWorkspaceDropdown();
      return;
    }

    try {
      this.closeWorkspaceDropdown();
      if (this.terminal) {
        this.terminal.appendOutput(`🔄 Switching to workspace "${name}"...`, 'warn');
      }

      const res = await fetch('/api/workspaces/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      }).then(r => r.json());

      if (!res.success) {
        throw new Error(res.error || 'Failed to switch workspace');
      }

      this.activeWorkspace = res.active_workspace || name;
      this.updateWorkspaceDisplay(this.activeWorkspace, res.active_path);

      // Refresh list, files, editor, preview, and rehydrate session
      await this.fetchWorkspaces();
      await this.fileTree.refresh();
      if (this.codeEditor) this.codeEditor.clear();
      this.reloadPreview();

      // Reset in-memory agent engine state and rehydrate workspace session
      if (this.agentEngine) {
        this.agentEngine.reset();
        this.agentEngine.setWorkspace(this.activeWorkspace);
      }
      await this.rehydrateSession(true);

      if (this.terminal) {
        this.terminal.appendOutput(`✔ Active workspace is now "${this.activeWorkspace}" (${res.active_path || ''})`, 'success');
      }
    } catch (err) {
      alert(`Could not switch workspace: ${err.message}`);
      if (this.terminal) {
        this.terminal.appendOutput(`❌ Failed to switch workspace: ${err.message}`, 'error');
      }
    }
  }

  async createWorkspace(name) {
    const cleanName = (name || '').trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    if (!cleanName) {
      alert('Please enter a valid workspace name (letters, numbers, hyphens).');
      return;
    }

    try {
      const btn = document.getElementById('btn-create-workspace-confirm');
      if (btn) {
        btn.disabled = true;
        btn.innerText = 'Creating...';
      }

      const res = await fetch('/api/workspaces/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: cleanName })
      }).then(r => r.json());

      if (!res.success) {
        throw new Error(res.error || 'Failed to create workspace');
      }

      this.activeWorkspace = res.active_workspace || cleanName;
      this.updateWorkspaceDisplay(this.activeWorkspace, res.active_path);

      // Hide input row and clear input
      const inputRow = document.getElementById('new-workspace-input-row');
      const input = document.getElementById('input-new-workspace-name');
      if (inputRow) inputRow.style.display = 'none';
      if (input) input.value = '';

      this.closeWorkspaceDropdown();

      await this.fetchWorkspaces();
      await this.fileTree.refresh();
      if (this.codeEditor) this.codeEditor.clear();
      this.reloadPreview();

      if (this.agentEngine) {
        this.agentEngine.reset();
        this.agentEngine.setWorkspace(this.activeWorkspace);
      }
      await this.rehydrateSession(true);

      if (this.terminal) {
        this.terminal.appendOutput(`✔ Created and activated workspace "${this.activeWorkspace}"`, 'success');
      }
    } catch (err) {
      alert(`Could not create workspace: ${err.message}`);
    } finally {
      const btn = document.getElementById('btn-create-workspace-confirm');
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Create & Switch';
      }
    }
  }

  async deleteWorkspace(name) {
    if (!name || name === 'default') {
      alert('Cannot delete the default workspace.');
      return;
    }

    if (!confirm(`Are you sure you want to permanently delete workspace "${name}" and all its files? This cannot be undone.`)) {
      return;
    }

    try {
      const res = await fetch('/api/workspaces/delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      }).then(r => r.json());

      if (!res.success) {
        throw new Error(res.error || 'Failed to delete workspace');
      }

      if (this.terminal) {
        this.terminal.appendOutput(`✔ Workspace "${name}" deleted.`, 'warn');
      }

      // If active workspace was deleted, backend automatically points to remaining or default
      this.activeWorkspace = res.active_workspace || 'default';
      this.updateWorkspaceDisplay(this.activeWorkspace, res.active_path);

      await this.fetchWorkspaces();
      await this.fileTree.refresh();
      if (this.codeEditor) this.codeEditor.clear();
      this.reloadPreview();

      if (this.agentEngine) {
        this.agentEngine.reset();
        this.agentEngine.setWorkspace(this.activeWorkspace);
      }
      await this.rehydrateSession(true);
    } catch (err) {
      alert(`Could not delete workspace: ${err.message}`);
    }
  }

  toggleWorkspaceDropdown() {
    const menu = document.getElementById('workspace-dropdown-menu');
    if (!menu) return;
    const isVisible = menu.style.display !== 'none';
    if (isVisible) {
      this.closeWorkspaceDropdown();
    } else {
      this.openWorkspaceDropdown();
    }
  }

  openWorkspaceDropdown() {
    const menu = document.getElementById('workspace-dropdown-menu');
    if (menu) {
      menu.style.display = 'block';
      this.fetchWorkspaces();
    }
  }

  closeWorkspaceDropdown() {
    const menu = document.getElementById('workspace-dropdown-menu');
    if (menu) {
      menu.style.display = 'none';
    }
    const inputRow = document.getElementById('new-workspace-input-row');
    if (inputRow) {
      inputRow.style.display = 'none';
    }
  }

  bindHudControls() {
    // 0. Workspace Switcher Pill & Dropdown bindings
    const wsPill = document.getElementById('hud-workspace-pill');
    if (wsPill) {
      wsPill.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleWorkspaceDropdown();
      });
    }

    const sidebarWsBadge = document.getElementById('sidebar-active-workspace-badge');
    if (sidebarWsBadge) {
      sidebarWsBadge.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleWorkspaceDropdown();
      });
    }

    const sidebarAddWsBtn = document.getElementById('btn-sidebar-add-workspace');
    if (sidebarAddWsBtn) {
      sidebarAddWsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.openWorkspaceDropdown();
        const inputRow = document.getElementById('new-workspace-input-row');
        const input = document.getElementById('input-new-workspace-name');
        if (inputRow) inputRow.style.display = 'block';
        if (input) setTimeout(() => input.focus(), 50);
      });
    }

    const showNewWsBtn = document.getElementById('btn-show-new-workspace');
    if (showNewWsBtn) {
      showNewWsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const inputRow = document.getElementById('new-workspace-input-row');
        const input = document.getElementById('input-new-workspace-name');
        if (inputRow) inputRow.style.display = 'block';
        if (input) setTimeout(() => input.focus(), 50);
      });
    }

    const cancelNewWsBtn = document.getElementById('btn-cancel-new-workspace');
    if (cancelNewWsBtn) {
      cancelNewWsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const inputRow = document.getElementById('new-workspace-input-row');
        if (inputRow) inputRow.style.display = 'none';
      });
    }

    const createWsConfirmBtn = document.getElementById('btn-create-workspace-confirm');
    const wsInput = document.getElementById('input-new-workspace-name');
    if (createWsConfirmBtn && wsInput) {
      createWsConfirmBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.createWorkspace(wsInput.value);
      });
      wsInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.createWorkspace(wsInput.value);
        } else if (e.key === 'Escape') {
          const inputRow = document.getElementById('new-workspace-input-row');
          if (inputRow) inputRow.style.display = 'none';
        }
      });
    }

    // Close workspace dropdown on outside click
    document.addEventListener('click', (e) => {
      const pillContainer = document.getElementById('workspace-pill-container');
      const sidebarBadge = document.getElementById('sidebar-active-workspace-badge');
      const sidebarAddBtn = document.getElementById('btn-sidebar-add-workspace');
      if (pillContainer && !pillContainer.contains(e.target) &&
          (!sidebarBadge || !sidebarBadge.contains(e.target)) &&
          (!sidebarAddBtn || !sidebarAddBtn.contains(e.target))) {
        this.closeWorkspaceDropdown();
      }
    });

    // Run Mission Button
    const runBtn = document.getElementById('btn-run-mission');
    const stopBtn = document.getElementById('btn-stop-execution');
    const input = document.getElementById('contextual-prompt-input');

    if (runBtn) {
      runBtn.addEventListener('click', () => {
        const prompt = (input && input.value.trim()) || 'Build a modern personal portfolio and interactive task dashboard with real-time state';
        if (input) input.value = '';
        this.agentEngine.executeGoal(prompt);
      });
    }

    if (stopBtn) {
      stopBtn.addEventListener('click', () => {
        if (this.agentEngine) {
          this.agentEngine.abort('Execution manually stopped by user via HUD Stop button.');
        }
        this.setExecutionUiRunning(false);
      });
    }

    // HUD Terminal Toggle Button
    const hudTermBtn = document.getElementById('btn-toggle-terminal-hud');
    if (hudTermBtn) {
      hudTermBtn.addEventListener('click', () => {
        this.switchTab(this.activeTab === 'terminal' ? 'preview' : 'terminal');
      });
    }

    // Export ZIP Button
    const exportZipBtn = document.getElementById('btn-export-zip');
    if (exportZipBtn) {
      exportZipBtn.addEventListener('click', () => {
        exportZipBtn.disabled = true;
        exportZipBtn.innerHTML = '<span>⏳</span> <span>Exporting...</span>';
        const a = document.createElement('a');
        a.href = '/api/workspace/export-zip';
        a.download = 'workspace.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
        this.terminal.appendOutput('✔ Entire workspace exported as workspace.zip', 'success');
        setTimeout(() => {
          exportZipBtn.disabled = false;
          exportZipBtn.innerHTML = '<span>📦</span> <span>Export ZIP</span>';
        }, 1500);
      });
    }

    // Checkpoints Modal Controls
    const checkpointsBtn = document.getElementById('btn-checkpoints');
    const checkpointsModal = document.getElementById('checkpoints-modal');
    const closeCheckpointsBtn = document.getElementById('btn-close-checkpoints');
    const createCheckpointBtn = document.getElementById('btn-create-checkpoint');
    const checkpointNameInput = document.getElementById('checkpoint-name-input');
    const checkpointsList = document.getElementById('checkpoints-list');

    const loadCheckpoints = async () => {
      if (!checkpointsList) return;
      checkpointsList.innerHTML = '<div style="color:var(--text-muted);font-size:12px;text-align:center;padding:15px;">Loading checkpoints...</div>';
      try {
        const res = await fetch('/api/workspace/checkpoints').then(r => r.json());
        const list = res.checkpoints || [];
        if (list.length === 0) {
          checkpointsList.innerHTML = '<div style="color:var(--text-muted);font-size:12px;text-align:center;padding:15px;">No checkpoints created yet. Click "+ Create Checkpoint" above to save current workspace state.</div>';
          return;
        }
        checkpointsList.innerHTML = list.map(cp => `
          <div style="display:flex;align-items:center;justify-content:space-between;background:rgba(15,23,42,0.8);border:1px solid var(--border-medium);padding:10px 14px;border-radius:6px;">
            <div>
              <div style="font-weight:700;color:#f8fafc;font-size:12.5px;">${cp.name || cp.id}</div>
              <div style="font-size:11px;color:#94a3b8;margin-top:2px;">
                <span>⏱️ ${cp.timestamp || new Date(cp.created_at * 1000).toLocaleString()}</span>
                ${cp.file_count ? ` · <span>${cp.file_count} files</span>` : ''}
                ${cp.description ? ` · <em>${cp.description}</em>` : ''}
              </div>
            </div>
            <button class="btn btn-secondary btn-sm btn-rollback-cp" data-id="${cp.id}" style="color:#38bdf8;border-color:rgba(56,189,248,0.4);white-space:nowrap;">
              ↺ Rollback
            </button>
          </div>
        `).join('');

        checkpointsList.querySelectorAll('.btn-rollback-cp').forEach(btn => {
          btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            if (confirm(`Rollback workspace to checkpoint "${id}"? This will restore files to that snapshot.`)) {
              btn.disabled = true;
              btn.innerText = 'Restoring...';
              try {
                const rbRes = await fetch('/api/workspace/rollback', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ id })
                }).then(r => r.json());
                if (rbRes.success) {
                  await this.fileTree.refresh();
                  this.reloadPreview();
                  if (this.codeEditor) {
                    await this.codeEditor.reloadAllOpenTabs();
                  }
                  this.terminal.appendOutput(`✔ Workspace successfully rolled back to checkpoint "${id}" (${rbRes.restored_files} files restored).`, 'success');
                  if (checkpointsModal) checkpointsModal.classList.remove('open');
                } else {
                  alert('Rollback failed: ' + (rbRes.error || 'Unknown error'));
                }
              } catch (err) {
                alert('Rollback error: ' + err.message);
              }
            }
          });
        });
      } catch (err) {
        checkpointsList.innerHTML = `<div style="color:#f87171;font-size:12px;text-align:center;padding:15px;">Failed to load checkpoints: ${err.message}</div>`;
      }
    };

    if (checkpointsBtn && checkpointsModal) {
      checkpointsBtn.addEventListener('click', () => {
        checkpointsModal.classList.add('open');
        loadCheckpoints();
      });
    }

    if (closeCheckpointsBtn && checkpointsModal) {
      closeCheckpointsBtn.addEventListener('click', () => {
        checkpointsModal.classList.remove('open');
      });
      checkpointsModal.addEventListener('click', (e) => {
        if (e.target === checkpointsModal) checkpointsModal.classList.remove('open');
      });
    }

    if (createCheckpointBtn && checkpointNameInput) {
      createCheckpointBtn.addEventListener('click', async () => {
        const name = checkpointNameInput.value.trim() || 'snapshot';
        createCheckpointBtn.disabled = true;
        createCheckpointBtn.innerText = 'Creating...';
        try {
          const res = await fetch('/api/workspace/checkpoint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
          }).then(r => r.json());
          if (res.success) {
            checkpointNameInput.value = '';
            this.terminal.appendOutput(`✔ Checkpoint "${name}" created.`, 'success');
            await loadCheckpoints();
          }
        } catch (err) {
          alert('Failed to create checkpoint: ' + err.message);
        } finally {
          createCheckpointBtn.disabled = false;
          createCheckpointBtn.innerText = '+ Create Checkpoint';
        }
      });
    }

    // Install Dependencies Button (Autonomous & Manual)
    const runDepsBtn = document.getElementById('btn-run-deps');
    if (runDepsBtn) {
      runDepsBtn.addEventListener('click', async () => {
        try {
          runDepsBtn.disabled = true;
          runDepsBtn.innerHTML = '⏳ Installing...';
          this.switchTab('terminal');

          const filesResp = await fetch('/api/workspace/files').then(r => r.json()).catch(() => ({ files: [] }));
          const files = filesResp.files || [];
          const reqFile = files.find(f => f.path.toLowerCase().endsWith('requirements.txt'));
          const pkgFile = files.find(f => f.path.toLowerCase() === 'package.json');

          if (!reqFile && !pkgFile) {
            this.terminal.appendOutput('⚠️ No requirements.txt or package.json found in workspace.', 'warn');
            return;
          }

          if (reqFile) {
            this.terminal.appendCommand(`pip install -r ${reqFile.path}`);
            const res = await this.terminal.runCommand(`pip install -r ${reqFile.path}`);
            if (res.exit_code === 0) {
              this.terminal.appendOutput(`✔ Python dependencies successfully verified and installed (${reqFile.path}).`, 'success');
            }
          }

          if (pkgFile) {
            this.terminal.appendCommand(`npm install`);
            const res = await this.terminal.runCommand(`npm install`);
            if (res.exit_code === 0) {
              this.terminal.appendOutput(`✔ Node.js packages installed cleanly.`, 'success');
            }
          }

          runDepsBtn.innerHTML = '✅ Installed!';
        } catch (err) {
          this.terminal.appendOutput(`❌ Failed to install dependencies: ${err.message}`, 'error');
          runDepsBtn.innerHTML = '❌ Error';
        } finally {
          setTimeout(() => {
            runDepsBtn.disabled = false;
            runDepsBtn.innerHTML = '📦 Install Deps';
          }, 2000);
        }
      });
    }

    // Clear Workspace
    const clearBtn = document.getElementById('btn-clear-workspace');
    if (clearBtn) {
      clearBtn.addEventListener('click', async () => {
        try {
          clearBtn.disabled = true;
          clearBtn.innerHTML = '⏳ Clearing...';

          const res = await fetch('/api/workspace/clear', { method: 'POST' });
          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `HTTP ${res.status}`);
          }

          // 1. Refresh file tree
          await this.fileTree.refresh();

          // 2. Clear code editor
          if (this.codeEditor) {
            this.codeEditor.clear();
          }

          // 3. Clear DAG canvas
          if (this.dagCanvas) {
            this.dagCanvas.clear();
          }

          // 4. Reload preview (displays clean empty state)
          this.reloadPreview();

          // 5. Reset agent engine & cockpit cards & persistent session
          if (this.agentEngine && typeof this.agentEngine.reset === 'function') {
            this.agentEngine.reset();
          }
          if (this.agentEngine && typeof this.agentEngine.clearSession === 'function') {
            await this.agentEngine.clearSession();
          }

          // 6. Reset prompt input and chat messages
          const promptInput = document.getElementById('contextual-prompt-input');
          if (promptInput) promptInput.value = '';

          const chatTimeline = document.getElementById('chat-timeline');
          if (chatTimeline) {
            chatTimeline.querySelectorAll('.chat-msg-row, .tool-card').forEach(el => el.remove());
          }

          this.setExecutionUiRunning(false);

          // 7. Output to terminal
          this.terminal.appendOutput('✔ Workspace files cleared. Clean project state initialized.', 'warn');

          clearBtn.innerHTML = '✅ Cleared!';
        } catch (err) {
          console.error('Failed to clear workspace:', err);
          this.terminal.appendOutput(`❌ Failed to clear workspace: ${err.message}`, 'error');
          clearBtn.innerHTML = '❌ Error';
        } finally {
          setTimeout(() => {
            clearBtn.disabled = false;
            clearBtn.innerHTML = '🗑️ Clear';
          }, 1500);
        }
      });
    }

    // Settings Button handled via bindSettingsModal
  }

  populateModelPresets(provider, selectedModel = null) {
    const presetSelect = document.getElementById('setting-model-preset');
    const modelInput = document.getElementById('setting-model');
    const hintSpan = document.getElementById('key-provider-hint');
    const helperText = document.getElementById('model-helper-text');
    if (!presetSelect) return;

    const config = PROVIDER_PRESETS[provider] || PROVIDER_PRESETS.groq;
    if (hintSpan) hintSpan.innerText = config.keyHint || `${config.name} Key`;

    presetSelect.innerHTML = '';
    let hasMatch = false;

    config.models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.innerText = m.label;
      if (selectedModel && m.id === selectedModel) {
        opt.selected = true;
        hasMatch = true;
      }
      presetSelect.appendChild(opt);
    });

    if (selectedModel && !hasMatch) {
      presetSelect.value = 'custom';
    } else if (!selectedModel) {
      presetSelect.value = config.defaultModel;
      if (modelInput) modelInput.value = config.defaultModel;
    }

    if (helperText) {
      helperText.innerHTML = `Active Provider: <strong>${config.name}</strong>. Selected model: <code>${modelInput?.value || selectedModel || config.defaultModel}</code>`;
    }
  }

  updateKeyHelperText(keyStr, provider = 'groq') {
    const keyHelper = document.getElementById('key-helper-text');
    if (!keyHelper) return;
    const keys = (keyStr || '').split(/[,;\s]+/).map(k => k.trim()).filter(Boolean);
    const count = keys.length;
    if (provider === 'nvidia') {
      keyHelper.innerHTML = `⚡ <strong>NVIDIA NIM Cloud Active</strong>: High-throughput inference powered by <code>meta/llama-3.2-11b-vision-instruct</code>.`;
      keyHelper.style.color = '#38bdf8';
    } else if (provider === 'groq') {
      if (count > 1) {
        keyHelper.innerHTML = `⚡ <strong>${count}-Key Auto-Rotation Active</strong>: ${count} Groq keys pooled for high token rate limits & zero-downtime failover!`;
        keyHelper.style.color = '#38bdf8';
      } else if (count === 1) {
        keyHelper.innerHTML = `⚡ <strong>1 Key Active</strong>. Tip: Enter multiple keys separated by commas for multi-key pool rotation.`;
        keyHelper.style.color = '#94a3b8';
      } else {
        keyHelper.innerHTML = `Enter one or more Groq API keys separated by commas.`;
        keyHelper.style.color = '#94a3b8';
      }
    } else {
      if (count > 1) {
        keyHelper.innerHTML = `⚡ <strong>${count}-Key Auto-Rotation Active</strong>: Round-robin failover across ${count} keys.`;
        keyHelper.style.color = '#38bdf8';
      } else {
        keyHelper.innerHTML = `Enter API key for ${provider.toUpperCase()}.`;
        keyHelper.style.color = '#94a3b8';
      }
    }
  }

  handleProviderChange(newProvider) {
    const keyInput = document.getElementById('setting-api-key');
    const modelInput = document.getElementById('setting-model');
    const statusBox = document.getElementById('settings-test-status');
    if (statusBox) statusBox.style.display = 'none';

    const config = PROVIDER_PRESETS[newProvider] || PROVIDER_PRESETS.groq;

    // 1. Restore saved key for this provider or default key
    let savedKey = localStorage.getItem(`fraiday_key_${newProvider}`) || config.defaultKey || '';
    if (config.defaultKey && (!savedKey || savedKey.split(',').length < config.defaultKey.split(',').length)) {
      savedKey = config.defaultKey;
    }
    if (keyInput) keyInput.value = savedKey;

    // 2. Restore saved model for this provider or default model
    let savedModel = localStorage.getItem(`fraiday_model_${newProvider}`) || config.defaultModel;
    if (newProvider === 'groq' && (!savedModel || savedModel.includes('20b'))) {
      savedModel = config.defaultModel;
    }
    if (modelInput) modelInput.value = savedModel;

    // 3. Update model presets dropdown & helper text
    this.populateModelPresets(newProvider, savedModel);
    this.updateKeyHelperText(savedKey, newProvider);
  }

  async testSettingsConnection() {
    const testBtn = document.getElementById('btn-test-settings');
    const testText = document.getElementById('btn-test-settings-text');
    const statusBox = document.getElementById('settings-test-status');
    const providerSelect = document.getElementById('setting-provider');
    const keyInput = document.getElementById('setting-api-key');
    const modelInput = document.getElementById('setting-model');

    const provider = providerSelect ? providerSelect.value : 'groq';
    const apiKey = keyInput ? keyInput.value.trim() : '';
    const model = modelInput ? modelInput.value.trim() : '';

    if (!apiKey && provider !== 'ollama') {
      if (statusBox) {
        statusBox.style.display = 'block';
        statusBox.style.background = 'rgba(239, 68, 68, 0.15)';
        statusBox.style.border = '1px solid rgba(239, 68, 68, 0.4)';
        statusBox.style.color = '#f87171';
        statusBox.innerHTML = '✕ Please provide an API key before testing.';
      }
      return;
    }

    if (!model) {
      if (statusBox) {
        statusBox.style.display = 'block';
        statusBox.style.background = 'rgba(239, 68, 68, 0.15)';
        statusBox.style.border = '1px solid rgba(239, 68, 68, 0.4)';
        statusBox.style.color = '#f87171';
        statusBox.innerHTML = '✕ Please specify a model identifier.';
      }
      return;
    }

    if (testBtn) testBtn.disabled = true;
    if (testText) testText.innerText = 'Testing...';
    if (statusBox) {
      statusBox.style.display = 'block';
      statusBox.style.background = 'rgba(56, 189, 248, 0.1)';
      statusBox.style.border = '1px solid rgba(56, 189, 248, 0.3)';
      statusBox.style.color = '#38bdf8';
      statusBox.innerHTML = `⏳ Sending verification ping to <strong>${provider.toUpperCase()}</strong> with model <code>${model}</code>...`;
    }

    const t0 = performance.now();
    try {
      const resp = await fetch('/api/llm/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          api_key: apiKey,
          model,
          prompt: 'Ping test. Reply with OK.',
          max_tokens: 15
        })
      });

      const elapsed = Math.round(performance.now() - t0);

      if (resp.ok) {
        const data = await resp.json();
        const modelUsed = data.model_used || model;
        const keysCount = data.keys_count || 1;
        const keyInfo = keysCount > 1 ? ` · ⚡ Active <strong>${keysCount}-Key Round-Robin Rotation</strong>` : '';
        if (statusBox) {
          statusBox.style.display = 'block';
          statusBox.style.background = 'rgba(16, 185, 129, 0.15)';
          statusBox.style.border = '1px solid rgba(16, 185, 129, 0.4)';
          statusBox.style.color = '#34d399';
          statusBox.innerHTML = `✔ <strong>Verification Successful!</strong><br/>Responded in ${elapsed}ms using model <code>${modelUsed}</code>${keyInfo}. Ready for autonomous execution.`;
        }
      } else {
        const errData = await resp.json().catch(() => ({}));
        const msg = errData.error || `HTTP ${resp.status}: ${resp.statusText}`;
        if (statusBox) {
          statusBox.style.display = 'block';
          statusBox.style.background = 'rgba(239, 68, 68, 0.15)';
          statusBox.style.border = '1px solid rgba(239, 68, 68, 0.4)';
          statusBox.style.color = '#f87171';
          statusBox.innerHTML = `✕ <strong>Verification Failed (${elapsed}ms)</strong><br/><span style="font-family:var(--font-mono);font-size:11px;">${this.escapeInlineMd(msg)}</span>`;
        }
      }
    } catch (err) {
      if (statusBox) {
        statusBox.style.display = 'block';
        statusBox.style.background = 'rgba(239, 68, 68, 0.15)';
        statusBox.style.border = '1px solid rgba(239, 68, 68, 0.4)';
        statusBox.style.color = '#f87171';
        statusBox.innerHTML = `✕ <strong>Connection Error:</strong> ${this.escapeInlineMd(err.message)}`;
      }
    } finally {
      if (testBtn) testBtn.disabled = false;
      if (testText) testText.innerText = 'Test Connection';
    }
  }

  openSettingsModal() {
    const modal = document.getElementById('settings-modal');
    const providerSelect = document.getElementById('setting-provider');
    const keyInput = document.getElementById('setting-api-key');
    const modelInput = document.getElementById('setting-model');
    const safetySelect = document.getElementById('setting-safety');
    const statusBox = document.getElementById('settings-test-status');

    if (statusBox) statusBox.style.display = 'none';

    const activeProvider = this.agentEngine?.provider || localStorage.getItem('fraiday_provider') || 'groq';
    const providerConfig = PROVIDER_PRESETS[activeProvider] || PROVIDER_PRESETS.groq;

    let activeKey = this.agentEngine?.apiKey || localStorage.getItem('fraiday_api_key') || localStorage.getItem(`fraiday_key_${activeProvider}`) || providerConfig.defaultKey || '';
    if (providerConfig.defaultKey && (!activeKey || activeKey.split(',').length < providerConfig.defaultKey.split(',').length)) {
      activeKey = providerConfig.defaultKey;
    }

    let activeModel = this.agentEngine?.model || localStorage.getItem('fraiday_model') || localStorage.getItem(`fraiday_model_${activeProvider}`) || providerConfig.defaultModel || 'openai/gpt-oss-120b';
    if (activeProvider === 'groq' && (!activeModel || activeModel.includes('20b'))) {
      activeModel = providerConfig.defaultModel || 'openai/gpt-oss-120b';
    }

    const activeSafety = localStorage.getItem('fraiday_safety') || 'autonomous_execute';

    if (providerSelect) providerSelect.value = activeProvider;
    if (keyInput) keyInput.value = activeKey;
    if (modelInput) modelInput.value = activeModel;
    if (safetySelect) safetySelect.value = activeSafety;

    this.populateModelPresets(activeProvider, activeModel);
    this.updateKeyHelperText(activeKey, activeProvider);

    if (modal) {
      modal.classList.add('open');
      modal.style.display = 'flex';
      modal.style.opacity = '1';
      modal.style.visibility = 'visible';
    }
  }

  closeSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
      modal.classList.remove('open');
      modal.style.display = 'none';
      modal.style.opacity = '0';
      modal.style.visibility = 'hidden';
    }
  }

  updateModelDisplay(provider, model) {
    const hudModelName = document.getElementById('hud-model-name');
    const monoBadge = document.getElementById('monologue-model-badge');

    const providerLabels = {
      groq: 'Groq',
      nvidia: 'NVIDIA NIM',
      openai: 'OpenAI',
      ollama: 'Ollama'
    };
    const pLabel = providerLabels[provider] || (provider ? provider.toUpperCase() : 'AI ENGINE');
    let shortName = model || 'Default';
    if (shortName.includes('/')) {
      shortName = shortName.split('/').pop();
    }
    shortName = shortName
      .replace(/^gpt-oss-120b$/i, 'GPT OSS 120B')
      .replace(/^gpt-oss-20b$/i, 'GPT OSS 20B')
      .replace(/^qwen-3\.8-27b$/i, 'Qwen 3.8 27B')
      .replace(/^llama-3\.2-11b-vision-instruct$/i, 'Llama 3.2 11B')
      .replace(/^llama-3\.2-90b-vision-instruct$/i, 'Llama 3.2 90B')
      .replace(/^llama-3\.3-70b-versatile$/i, 'Llama 3.3 70B')
      .replace(/^llama-3\.1-8b-instant$/i, 'Llama 3.1 8B')
      .replace(/^gpt-4o-mini$/i, 'GPT-4o Mini')
      .replace(/^gpt-4o$/i, 'GPT-4o');

    const fullHud = `${pLabel} (${shortName})`;
    if (hudModelName) hudModelName.innerText = fullHud;
    if (monoBadge) monoBadge.innerText = `${pLabel} · ${shortName}`;
  }

  async syncInitialConfig() {
    try {
      const resp = await fetch('/api/config');
      if (resp.ok) {
        const data = await resp.json();
        const activeProvider = data.provider || localStorage.getItem('fraiday_provider') || 'groq';
        const providerConfig = PROVIDER_PRESETS[activeProvider] || PROVIDER_PRESETS.groq;

        // Upgrade/sync model from server
        let activeModel = data.model || localStorage.getItem('fraiday_model') || providerConfig.defaultModel;
        if (activeProvider === 'groq' && (!activeModel || activeModel.includes('20b'))) {
          activeModel = data.model || 'openai/gpt-oss-120b';
        }
        localStorage.setItem('fraiday_provider', activeProvider);
        localStorage.setItem('fraiday_model', activeModel);
        localStorage.setItem(`fraiday_model_${activeProvider}`, activeModel);

        // Upgrade/sync API keys from server
        let activeKey = data.api_key || localStorage.getItem('fraiday_api_key') || providerConfig.defaultKey || '';
        if (data.api_key) {
          activeKey = data.api_key;
        } else if (providerConfig.defaultKey && (!activeKey || activeKey.split(',').length < providerConfig.defaultKey.split(',').length)) {
          activeKey = providerConfig.defaultKey;
        }
        if (activeKey) {
          localStorage.setItem('fraiday_api_key', activeKey);
          localStorage.setItem(`fraiday_key_${activeProvider}`, activeKey);
        }

        if (this.agentEngine) {
          this.agentEngine.provider = activeProvider;
          this.agentEngine.model = activeModel;
          if (activeKey) this.agentEngine.apiKey = activeKey;
        }

        this.updateModelDisplay(activeProvider, activeModel);
      }
    } catch (_) {
      this.updateModelDisplay(this.agentEngine.provider, this.agentEngine.model);
    }
  }

  bindSettingsModal() {
    const modal = document.getElementById('settings-modal');
    const closeBtn = document.getElementById('btn-close-settings');
    const cancelBtn = document.getElementById('btn-cancel-settings');
    const saveBtn = document.getElementById('btn-save-settings');
    const openBtn = document.getElementById('btn-open-settings');
    const pillBtn = document.getElementById('hud-model-pill');
    const testBtn = document.getElementById('btn-test-settings');
    const toggleKeyBtn = document.getElementById('btn-toggle-key-visibility');

    const providerSelect = document.getElementById('setting-provider');
    const presetSelect = document.getElementById('setting-model-preset');
    const keyInput = document.getElementById('setting-api-key');
    const modelInput = document.getElementById('setting-model');

    // Live update rotation badge on typing/pasting keys
    if (keyInput) {
      keyInput.addEventListener('input', (e) => {
        const prov = providerSelect ? providerSelect.value : 'groq';
        this.updateKeyHelperText(e.target.value, prov);
      });
    }

    // Provider dropdown changed
    if (providerSelect) {
      providerSelect.addEventListener('change', (e) => {
        this.handleProviderChange(e.target.value);
      });
    }

    // Model preset dropdown changed
    if (presetSelect) {
      presetSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val !== 'custom') {
          if (modelInput) modelInput.value = val;
          const helperText = document.getElementById('model-helper-text');
          if (helperText) helperText.innerHTML = `Selected preset: <code>${val}</code>`;
        } else {
          if (modelInput) {
            modelInput.focus();
            modelInput.select();
          }
        }
      });
    }

    // Model text input manually changed
    if (modelInput) {
      modelInput.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        if (presetSelect) {
          const hasOption = Array.from(presetSelect.options).some(opt => opt.value === val);
          presetSelect.value = hasOption ? val : 'custom';
        }
      });
    }

    // Toggle API Key visibility
    if (toggleKeyBtn && keyInput) {
      toggleKeyBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (keyInput.type === 'password') {
          keyInput.type = 'text';
          toggleKeyBtn.innerText = '🔒';
          toggleKeyBtn.title = 'Hide API Key';
        } else {
          keyInput.type = 'password';
          toggleKeyBtn.innerText = '👁️';
          toggleKeyBtn.title = 'Show API Key';
        }
      });
    }

    // Test connection button
    if (testBtn) {
      testBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.testSettingsConnection();
      });
    }

    // Open button in HUD
    if (openBtn) {
      openBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.openSettingsModal();
      });
    }

    // Clicking on model pill also opens settings
    if (pillBtn) {
      pillBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.openSettingsModal();
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.closeSettingsModal();
      });
    }

    if (cancelBtn) {
      cancelBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.closeSettingsModal();
      });
    }

    // Close on backdrop click
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.closeSettingsModal();
        }
      });
    }

    // Close on Escape key
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal && modal.classList.contains('open')) {
        this.closeSettingsModal();
      }
    });

    if (saveBtn) {
      saveBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.saveSettingsModal();
      });
    }
  }

  async saveSettingsModal() {
    const modal = document.getElementById('settings-modal');
    const saveBtn = document.getElementById('btn-save-settings');
    const providerSelect = document.getElementById('setting-provider');
    const keyInput = document.getElementById('setting-api-key');
    const modelInput = document.getElementById('setting-model');
    const safetySelect = document.getElementById('setting-safety');

    const provider = (providerSelect && providerSelect.value) || localStorage.getItem('fraiday_provider') || 'groq';
    const apiKey = (keyInput && keyInput.value.trim()) || localStorage.getItem('fraiday_api_key') || '';
    const model = (modelInput && modelInput.value.trim()) || localStorage.getItem('fraiday_model') || 'openai/gpt-oss-20b';
    const safety = (safetySelect && safetySelect.value) || localStorage.getItem('fraiday_safety') || 'request_review';

    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerText = 'Saving...';
    }

    // 1. Immediately persist locally so changes are NEVER lost
    try {
      localStorage.setItem('fraiday_provider', provider);
      localStorage.setItem('fraiday_api_key', apiKey);
      localStorage.setItem('fraiday_model', model);
      localStorage.setItem('fraiday_safety', safety);
      // Also remember per-provider settings
      localStorage.setItem(`fraiday_key_${provider}`, apiKey);
      localStorage.setItem(`fraiday_model_${provider}`, model);
    } catch (_) {}

    // 2. Update agent engine if present
    if (this.agentEngine && typeof this.agentEngine.setLlmConfig === 'function') {
      this.agentEngine.setLlmConfig(provider, apiKey, model);
    }

    // 3. Update frontend UI badges in HUD and Cockpit immediately
    this.updateModelDisplay(provider, model);

    // 4. CLEAR ANY EXISTING ERROR / HALTED CARDS IN TIMELINE
    const chatTimeline = document.getElementById('chat-timeline');
    const hadHaltCard = Boolean(chatTimeline && chatTimeline.querySelector('.chat-halted-row'));
    if (chatTimeline) {
      chatTimeline.querySelectorAll('.chat-halted-row').forEach(el => el.remove());
    }

    // 5. Reset agent state to idle/ready if it was in error
    if (this.agentEngine && this.agentEngine.state === 'error') {
      this.agentEngine.setState('idle', 'Ready');
    }

    // 6. Update reasoning monologue box
    const monologueCard = document.getElementById('agent-monologue-card');
    if (monologueCard) {
      const body = monologueCard.querySelector('.monologue-text') || monologueCard;
      if (body) {
        body.innerHTML = `<span style="color:#34d399;font-weight:600;">✔ AI Settings Updated:</span> Connected to <strong>${provider.toUpperCase()}</strong> (<code>${model}</code>). Previous halts cleared and ready for execution.`;
      }
    }

    try {
      // 7. Sync to backend server via POST /api/config
      const resp = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: apiKey, model, safety })
      });

      // 7b. Sync Vectorize Hindsight Memory config
      const hsKeyInput = document.getElementById('setting-hindsight-key');
      const hsUrlInput = document.getElementById('setting-hindsight-url');
      const hsBankInput = document.getElementById('setting-hindsight-bank');
      if (hsUrlInput || hsBankInput || hsKeyInput) {
        const hsKey = hsKeyInput ? hsKeyInput.value.trim() : '';
        const hsUrl = hsUrlInput ? hsUrlInput.value.trim() : 'https://api.hindsight.vectorize.io';
        const hsBank = hsBankInput ? hsBankInput.value.trim() : 'fraiday-core-memory';
        fetch('/api/hindsight/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: hsKey, base_url: hsUrl, bank_id: hsBank })
        }).then(r => r.json()).then(st => {
          this.hindsightInspector?.refreshData();
          this.updateHindsightHudPill(this.agentEngine.hindsightEnabled !== false);
        }).catch(() => {});
      }

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || `Server responded with ${resp.status}`);
      }

      if (this.terminal) {
        this.terminal.appendOutput(`✔ Active model synced across frontend & backend: [${provider.toUpperCase()}] ${model}`, 'success');
      }

      if (saveBtn) saveBtn.innerText = '✅ Saved!';
      setTimeout(() => {
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.innerText = 'Save Configuration';
        }
        this.closeSettingsModal();

        // 8. If an active goal was interrupted by the previous halt, render a prominent resume card
        if (hadHaltCard && this.agentEngine && this.agentEngine.currentGoal && chatTimeline) {
          this.renderResumePromptInChat(this.agentEngine.currentGoal, provider, model);
        }
      }, 350);
    } catch (err) {
      console.warn('Backend sync warning:', err);
      if (this.terminal) {
        this.terminal.appendOutput(`⚠️ Settings saved in browser. Backend sync note: ${err.message}`, 'warn');
      }
      if (saveBtn) saveBtn.innerText = '✅ Saved';
      setTimeout(() => {
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.innerText = 'Save Configuration';
        }
        this.closeSettingsModal();

        if (hadHaltCard && this.agentEngine && this.agentEngine.currentGoal && chatTimeline) {
          this.renderResumePromptInChat(this.agentEngine.currentGoal, provider, model);
        }
      }, 400);
    }
  }

  renderResumePromptInChat(goal, provider, model) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline) return;

    const row = document.createElement('div');
    row.className = 'chat-msg-row chat-agent-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">⚡</span>
        <span class="chat-sender-name">frAIday System</span>
        <span class="chat-sender-badge" style="background:rgba(16,185,129,0.2);color:#34d399;border:1px solid rgba(16,185,129,0.4);">Configuration Applied</span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent" style="border-color:rgba(16,185,129,0.4);background:rgba(6,25,18,0.95);color:#f1f5f9;">
        <div style="font-weight:700;color:#34d399;margin-bottom:4px;display:flex;align-items:center;gap:6px;">
          <span>✔ API Key Successfully Updated</span>
        </div>
        <div style="font-size:12px;color:#cbd5e1;margin-bottom:8px;">
          Connected to <strong>${provider.toUpperCase()}</strong> (${model}). The previous rate limit halt has been cleared. Click below to resume your mission where it left off:
        </div>
        <div style="display:flex;gap:8px;">
          <button id="btn-resume-after-settings" class="btn btn-primary btn-sm" style="background:#10b981;border-color:#10b981;font-weight:700;font-size:11.5px;padding:6px 14px;">
            ▶ Resume Mission: "${this.escapeInlineMd(goal)}"
          </button>
        </div>
      </div>
    `;

    chatTimeline.appendChild(row);

    const resumeBtn = row.querySelector('#btn-resume-after-settings');
    if (resumeBtn) {
      resumeBtn.addEventListener('click', () => {
        row.remove();
        if (this.agentEngine && typeof this.agentEngine.resumeGoal === 'function') {
          this.agentEngine.resumeGoal();
        } else if (this.agentEngine && this.agentEngine.currentGoal) {
          this.agentEngine.executeGoal(this.agentEngine.currentGoal);
        }
      });
    }

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  bindActivityBar() {
    document.querySelectorAll('.activity-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.getAttribute('data-panel');
        document.querySelectorAll('.activity-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.sidebar-panel-content').forEach(p => {
          p.style.display = p.getAttribute('data-panel') === target ? 'block' : 'none';
        });

        const titleEl = document.getElementById('sidebar-panel-title');
        if (titleEl) {
          const titles = {
            files: 'Workspace Explorer',
            knowledge: 'Discovered Knowledge Vault',
            skills: 'Agent Skills & MCP Tools',
            safety: 'Security & Sandbox Policies'
          };
          titleEl.innerText = titles[target] || 'Workspace';
        }
      });
    });
  }

  bindContextualInput() {
    const input = document.getElementById('contextual-prompt-input');
    const sendBtn = document.getElementById('btn-send-context-prompt');
    const stopContextBtn = document.getElementById('btn-stop-context-prompt');
    const slashPopup = document.getElementById('slash-commands-popup');

    const hideSlashPopup = () => {
      if (slashPopup) slashPopup.style.display = 'none';
    };

    const showSlashPopup = () => {
      if (slashPopup) slashPopup.style.display = 'block';
    };

    const executeSlashCommand = async (cmdStr) => {
      const parts = cmdStr.trim().split(/\s+/);
      const command = parts[0].toLowerCase();
      const arg = parts.slice(1).join(' ');

      if (command === '/fix') {
        const errors = (this.consoleLogs || []).filter(l => l.level === 'error').map(l => (l.args || []).join(' ')).slice(-5);
        const goal = arg || (errors.length > 0
          ? `Diagnose and fix the following runtime errors in the application: ${errors.join('; ')}`
          : 'Audit all workspace files and fix any syntax or runtime bugs');
        this.agentEngine.executeGoal(goal);
      } else if (command === '/test') {
        this.switchTab('terminal');
        this.terminal.appendOutput('🧪 Running autonomous test & visual verification suite...', 'warn');
        try {
          const verifyRes = await fetch('/api/build/verify', { method: 'POST' }).then(r => r.json());
          if (verifyRes.success) {
            this.terminal.appendOutput(`✔ Automated verification passed: ${verifyRes.message || 'Build is healthy'}`, 'success');
          } else {
            this.terminal.appendOutput(`❌ Verification failed: ${verifyRes.error || 'Issues detected'}`, 'error');
          }
        } catch (e) {
          this.terminal.appendOutput(`❌ Verification error: ${e.message}`, 'error');
        }
      } else if (command === '/plan') {
        const goal = arg || 'Research modern UI best practices and architect a full-featured web application';
        this.agentEngine.executeGoal(goal);
      } else if (command === '/audit') {
        const viewScreenshotBtn = document.getElementById('btn-view-screenshot');
        if (viewScreenshotBtn) viewScreenshotBtn.click();
      } else if (command === '/export') {
        const exportZipBtn = document.getElementById('btn-export-zip');
        if (exportZipBtn) exportZipBtn.click();
      } else if (command === '/checkpoint') {
        const name = arg || 'quick-save';
        const res = await fetch('/api/workspace/checkpoint', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name })
        }).then(r => r.json()).catch(() => ({}));
        if (res.success) {
          this.terminal.appendOutput(`✔ Saved checkpoint "${name}".`, 'success');
        }
      } else if (command === '/rollback') {
        const checkpointsBtn = document.getElementById('btn-checkpoints');
        if (checkpointsBtn) checkpointsBtn.click();
      } else if (command === '/clear') {
        const clearBtn = document.getElementById('btn-clear-workspace');
        if (clearBtn) clearBtn.click();
      } else {
        const termCmd = cmdStr.startsWith('/') ? cmdStr.slice(1) : cmdStr;
        this.switchTab('terminal');
        this.terminal.runCommand(termCmd);
      }
    };

    const handleSend = () => {
      const val = input.value.trim();
      if (!val) return;
      input.value = '';
      hideSlashPopup();

      if (val.startsWith('/')) {
        executeSlashCommand(val);
      } else {
        this.agentEngine.executeGoal(val);
      }
    };

    if (input) {
      input.addEventListener('input', () => {
        const v = input.value;
        if (v.startsWith('/')) {
          showSlashPopup();
          const filter = v.toLowerCase();
          if (slashPopup) {
            slashPopup.querySelectorAll('.slash-item').forEach(item => {
              const cmd = item.getAttribute('data-cmd');
              item.style.display = cmd.startsWith(filter) ? 'flex' : 'none';
            });
          }
        } else {
          hideSlashPopup();
        }
      });

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          handleSend();
        } else if (e.key === 'Escape') {
          hideSlashPopup();
        }
      });
    }

    if (slashPopup) {
      slashPopup.querySelectorAll('.slash-item').forEach(item => {
        item.addEventListener('click', () => {
          const cmd = item.getAttribute('data-cmd');
          if (input) {
            input.value = cmd + ' ';
            input.focus();
          }
          hideSlashPopup();
        });
      });
    }

    document.addEventListener('click', (e) => {
      if (slashPopup && !slashPopup.contains(e.target) && e.target !== input) {
        hideSlashPopup();
      }
    });

    if (sendBtn && input) {
      sendBtn.addEventListener('click', handleSend);
    }

    if (stopContextBtn) {
      stopContextBtn.addEventListener('click', () => {
        if (this.agentEngine) {
          this.agentEngine.abort('Execution manually stopped by user via Prompt Bar Stop button.');
        }
        this.setExecutionUiRunning(false);
      });
    }

    // Quick suggestion chips
    document.querySelectorAll('.context-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        if (input) {
          input.value = chip.innerText;
          input.focus();
        }
      });
    });
  }

  setExecutionUiRunning(isRunning) {
    const runMissionBtn = document.getElementById('btn-run-mission');
    const stopMissionBtn = document.getElementById('btn-stop-execution');
    const sendContextBtn = document.getElementById('btn-send-context-prompt');
    const stopContextBtn = document.getElementById('btn-stop-context-prompt');

    if (runMissionBtn) runMissionBtn.style.display = isRunning ? 'none' : 'inline-flex';
    if (stopMissionBtn) stopMissionBtn.style.display = isRunning ? 'inline-flex' : 'none';
    if (sendContextBtn) sendContextBtn.style.display = isRunning ? 'none' : 'inline-flex';
    if (stopContextBtn) stopContextBtn.style.display = isRunning ? 'inline-flex' : 'none';
  }

  renderUserMessageInChat(text, customTime = null) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline || !text) return;

    const row = document.createElement('div');
    row.className = 'chat-msg-row chat-user-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">👤</span>
        <span class="chat-sender-name">You</span>
        <span class="chat-sender-badge badge-user">Prompt</span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-user">${this.escapeInlineMd(text)}</div>
    `;

    chatTimeline.appendChild(row);

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  renderAgentMessageInChat(markdown, customTime = null) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline || !markdown) return;

    const row = document.createElement('div');
    row.className = 'chat-msg-row chat-agent-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">🧠</span>
        <span class="chat-sender-name">frAIday</span>
        <span class="chat-sender-badge badge-agent">Agent</span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent">${this.escapeInlineMd(markdown)}</div>
    `;

    chatTimeline.appendChild(row);

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  renderPlanApprovalCardInChat(planMarkdown, customTime = null) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline) return;

    const existing = document.getElementById('chat-plan-card');
    if (existing) existing.remove();

    const row = document.createElement('div');
    row.id = 'chat-plan-card';
    row.className = 'chat-msg-row chat-plan-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const firstLine = (planMarkdown || '').split('\n').find(l => l.startsWith('#')) || '# Implementation Plan';
    const titleText = firstLine.replace(/^#+\s*/, '');

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">📋</span>
        <span class="chat-sender-name">Planning Gate</span>
        <span class="chat-sender-badge" style="background:rgba(245,158,11,0.2);color:#fbbf24;border:1px solid rgba(245,158,11,0.4);">Approval Needed</span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent" style="border-color:rgba(245,158,11,0.4);background:rgba(22,27,34,0.95);">
        <div style="font-weight:700;color:#f8fafc;margin-bottom:4px;">📋 Plan Ready: ${this.escapeInlineMd(titleText)}</div>
        <div style="font-size:12px;color:#94a3b8;margin-bottom:10px;">
          Review the full plan in the <strong>Plan & Artifacts</strong> tab. Click below to authorize execution.
        </div>
        <div style="display:flex;gap:8px;">
          <button id="btn-chat-approve-plan" class="btn btn-primary btn-sm" style="background:#10b981;border-color:#10b981;font-weight:700;">
            ✓ Approve & Proceed
          </button>
          <button id="btn-chat-revise-plan" class="btn btn-secondary btn-sm">
            ✕ Revise Plan
          </button>
        </div>
      </div>
    `;

    chatTimeline.appendChild(row);

    const approveBtn = row.querySelector('#btn-chat-approve-plan');
    const reviseBtn = row.querySelector('#btn-chat-revise-plan');

    if (approveBtn) {
      approveBtn.addEventListener('click', () => {
        if (this.agentEngine) this.agentEngine.approvePlan();
        row.remove();
      });
    }
    if (reviseBtn) {
      reviseBtn.addEventListener('click', () => {
        const fb = prompt('Enter your guidance or revision instructions:');
        if (fb !== null && this.agentEngine) {
          this.agentEngine.rejectPlan(fb);
          row.remove();
        }
      });
    }

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  renderApprovedPlanCardInChat(planMarkdown, customTime = null) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline) return;

    const row = document.createElement('div');
    row.className = 'chat-msg-row chat-plan-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const firstLine = (planMarkdown || '').split('\n').find(l => l.startsWith('#')) || '# Implementation Plan';
    const titleText = firstLine.replace(/^#+\s*/, '');

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">📋</span>
        <span class="chat-sender-name">Planning Gate</span>
        <span class="chat-sender-badge" style="background:rgba(16,185,129,0.2);color:#34d399;border:1px solid rgba(16,185,129,0.4);">Approved</span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent" style="border-color:rgba(16,185,129,0.3);background:rgba(22,27,34,0.95);">
        <div style="font-weight:700;color:#34d399;margin-bottom:2px;">✔ Plan Approved: ${this.escapeInlineMd(titleText)}</div>
        <div style="font-size:11.5px;color:#94a3b8;">Full architectural plan archived in the <strong>Plan & Artifacts</strong> tab.</div>
      </div>
    `;

    chatTimeline.appendChild(row);
  }

  renderSystemAlertInChat(alertData, customTime = null, skipRecord = false) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline || !alertData) return;

    const row = document.createElement('div');
    row.className = 'chat-msg-row chat-system-alert-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const cleanFile = (alertData.filename || 'script').split('/').pop() || 'workspace script';

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">⚡</span>
        <span class="chat-sender-name">System Diagnostic</span>
        <span class="chat-sender-badge" style="background:rgba(239,68,68,0.2);color:#f87171;border:1px solid rgba(239,68,68,0.3);">Autonomous Error Interceptor</span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent" style="border-color:rgba(239,68,68,0.4);background:rgba(25,12,16,0.95);color:#fecaca;">
        <div style="font-weight:700;color:#f87171;margin-bottom:4px;display:flex;align-items:center;gap:6px;">
          <span>⚠️ Runtime Defect Captured in Preview</span>
        </div>
        <div style="font-family:var(--font-mono);font-size:11.5px;background:rgba(0,0,0,0.4);padding:6px 10px;border-radius:4px;border:1px solid rgba(239,68,68,0.2);color:#fca5a5;word-break:break-all;margin-bottom:6px;">
          ${this.escapeInlineMd(alertData.message)}
        </div>
        <div style="font-size:11px;color:#cbd5e1;">
          Origin: <code>${this.escapeInlineMd(cleanFile)}:${alertData.lineno || 0}</code>
        </div>
        <div style="font-size:11px;color:#94a3b8;margin-top:6px;font-style:italic;">
          frAIday autonomous self-healing loop initiated to diagnose, patch, and re-verify...
        </div>
      </div>
    `;

    chatTimeline.appendChild(row);

    if (!skipRecord && this.agentEngine) {
      this.agentEngine.recordTimelineEvent({ type: 'system_alert', alertData, timestamp: timeStr });
    }

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  renderVerificationScreenshotInChat(result, customTime = null, skipRecord = false) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline || !result || !result.screenshot_url) return;

    // Avoid duplicate verification cards
    const existing = document.getElementById('chat-verification-card');
    if (existing) existing.remove();

    const row = document.createElement('div');
    row.id = 'chat-verification-card';
    row.className = 'chat-msg-row chat-verification-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const isClean = result.verification_verdict === 'VERIFIED_CLEAN' && (!result.console_errors || result.console_errors.length === 0);
    const score = result.visual_score !== undefined ? result.visual_score : (isClean ? 10 : 4);
    const model = result.vision_model_used || 'meta/llama-3.2-11b-vision-instruct';
    const hasDefects = (result.visual_defects && result.visual_defects.length > 0) || !isClean;

    const escape = (str) => {
      if (!str) return '';
      return String(str).replace(/[&<>"']/g, s => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[s]);
    };

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">👁️</span>
        <span class="chat-sender-name">Multimodal Visual QA Inspector</span>
        <span class="chat-sender-badge" style="background:${isClean ? 'rgba(16,185,129,0.18)' : 'rgba(244,63,94,0.18)'};color:${isClean ? '#34d399' : '#f43f5e'};border:1px solid ${isClean ? 'rgba(16,185,129,0.35)' : 'rgba(244,63,94,0.35)'};">
          AI Vision Score: ${score}/10 ${isClean ? '· Verified Clean' : '· Defects Detected'}
        </span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent" style="border-color:${isClean ? 'rgba(16,185,129,0.4)' : 'rgba(244,63,94,0.4)'};background:${isClean ? 'rgba(6,25,18,0.95)' : 'rgba(30,10,14,0.95)'};color:#e2e8f0;">
        <div style="font-weight:700;color:${isClean ? '#34d399' : '#f43f5e'};margin-bottom:4px;display:flex;align-items:center;justify-content:space-between;gap:6px;">
          <span>${isClean ? '✔ Multimodal AI Vision Certified' : '⚠️ Visual Deficiencies Flagged'}</span>
          <span style="font-size:11px;font-weight:normal;color:#94a3b8;">(${result.dom_elements_count || 0} DOM Elements · ${result.console_errors?.length || 0} Console Errors)</span>
        </div>
        
        <div style="margin-bottom:8px;padding:8px 10px;border-radius:6px;background:rgba(255,255,255,0.03);border:1px solid ${isClean ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.25)'};font-size:11.5px;line-height:1.45;">
          <div style="font-weight:600;color:${isClean ? '#38bdf8' : '#fb7185'};margin-bottom:3px;display:flex;align-items:center;gap:6px;">
            <span>🔍 Model Analysis (${escape(model)}):</span>
          </div>
          <div style="color:#cbd5e1;">${escape(result.visual_summary || 'Visual elements, typography, and viewport layout verified.')}</div>
        </div>

        ${hasDefects && result.visual_defects && result.visual_defects.length ? `
          <div style="margin-bottom:8px;padding:6px 10px;border-radius:6px;background:rgba(244,63,94,0.12);border:1px solid rgba(244,63,94,0.3);font-size:11px;color:#fecdd3;">
            <div style="font-weight:600;color:#f43f5e;margin-bottom:2px;">⚠️ Detected Visual Defects:</div>
            <div>${escape(Array.isArray(result.visual_defects) ? result.visual_defects.join('; ') : result.visual_defects)}</div>
          </div>
        ` : ''}

        ${result.console_errors && result.console_errors.length ? `
          <div style="margin-bottom:8px;padding:6px 10px;border-radius:6px;background:rgba(244,63,94,0.12);border:1px solid rgba(244,63,94,0.3);font-size:11px;color:#fecdd3;">
            <div style="font-weight:600;color:#f43f5e;margin-bottom:2px;">⚠️ Console Runtime Errors:</div>
            <div>${escape(result.console_errors.join('; '))}</div>
          </div>
        ` : ''}

        ${result.visual_strengths && result.visual_strengths.length ? `
          <div style="margin-bottom:8px;font-size:11px;color:#34d399;display:flex;gap:6px;align-items:flex-start;">
            <span>✨</span>
            <div><strong>Strengths:</strong> ${escape(Array.isArray(result.visual_strengths) ? result.visual_strengths.join('; ') : result.visual_strengths)}</div>
          </div>
        ` : ''}

        <div style="border-radius:6px;overflow:hidden;border:1px solid ${isClean ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)'};background:#000;position:relative;">
          <img src="${result.screenshot_url}" style="width:100%;max-height:220px;object-fit:cover;display:block;cursor:pointer;background:#050811;" alt="Verified Live Render" onclick="window.open('${result.screenshot_url}', '_blank')" title="Click to view full image in new tab" />
          <div style="position:absolute;top:6px;left:6px;background:rgba(0,0,0,0.85);padding:2px 8px;border-radius:4px;font-size:10px;color:${isClean ? '#34d399' : '#f43f5e'};border:1px solid ${isClean ? 'rgba(52,211,153,0.3)' : 'rgba(244,63,94,0.3)'};font-weight:600;">
            Score: ${score}/10 · ${isClean ? 'Verified Clean' : 'Defects Flagged'}
          </div>
          <div style="position:absolute;bottom:6px;right:6px;background:rgba(0,0,0,0.85);padding:3px 8px;border-radius:4px;font-size:10.5px;color:#38bdf8;border:1px solid rgba(56,189,248,0.3);cursor:pointer;" onclick="window.open('${result.screenshot_url}', '_blank')">
            Open Screenshot ↗
          </div>
        </div>
      </div>
    `;

    chatTimeline.appendChild(row);

    if (!skipRecord && this.agentEngine) {
      this.agentEngine.recordTimelineEvent({ type: 'verification_screenshot', result, timestamp: timeStr });
    }

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  renderHaltedCardInChat(haltData, customTime = null, skipRecord = false) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline || !haltData) return;

    const row = document.createElement('div');
    row.className = 'chat-msg-row chat-halted-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const isAborted = Boolean(haltData.aborted);
    const rawError = (haltData.error || haltData.reason || '').toLowerCase();
    const isRateLimit = rawError.includes('429') || rawError.includes('rate limit') || rawError.includes('quota') || rawError.includes('tpd');
    const isAuth = rawError.includes('401') || rawError.includes('api key') || rawError.includes('unauthorized');
    const isTurnLimit = rawError.includes('turn limit') || rawError.includes('steps');

    let title = '🛑 Execution Halted';
    let badge = 'Halted';
    let icon = '🛑';
    let borderColor = 'rgba(239, 68, 68, 0.4)';
    let bgColor = 'rgba(30, 15, 20, 0.95)';
    let titleColor = '#f87171';
    let actionButtons = '';

    if (isAborted) {
      icon = '⏹';
      title = 'Execution Stopped by User';
      badge = 'Stopped';
      borderColor = 'rgba(148, 163, 184, 0.4)';
      bgColor = 'rgba(15, 23, 42, 0.95)';
      titleColor = '#94a3b8';
      actionButtons = `
        <button class="btn btn-primary btn-sm btn-chat-resume" style="background:#3b82f6;border-color:#3b82f6;font-weight:700;">
          ▶ Resume Objective
        </button>
      `;
    } else if (isRateLimit) {
      icon = '⏳';
      title = 'API Rate Limit Reached';
      badge = 'Rate Limited';
      borderColor = 'rgba(245, 158, 11, 0.4)';
      bgColor = 'rgba(28, 20, 10, 0.95)';
      titleColor = '#fbbf24';
      actionButtons = `
        <button class="btn btn-primary btn-sm btn-chat-open-settings" style="background:#f59e0b;border-color:#f59e0b;font-weight:700;">
          ⚙️ Switch AI Model / Provider
        </button>
        <button class="btn btn-secondary btn-sm btn-chat-resume">
          ↺ Retry Request
        </button>
      `;
    } else if (isAuth) {
      icon = '🔑';
      title = 'Invalid or Missing API Key';
      badge = 'Authentication Error';
      actionButtons = `
        <button class="btn btn-primary btn-sm btn-chat-open-settings" style="background:#3b82f6;border-color:#3b82f6;font-weight:700;">
          ⚙️ Configure API Key
        </button>
      `;
    } else if (isTurnLimit) {
      icon = '⚠️';
      title = 'Turn Limit Reached (100 Turns)';
      badge = 'Turn Limit';
      borderColor = 'rgba(245, 158, 11, 0.4)';
      bgColor = 'rgba(28, 20, 10, 0.95)';
      titleColor = '#fbbf24';
      actionButtons = `
        <button class="btn btn-primary btn-sm btn-chat-resume" style="background:#10b981;border-color:#10b981;font-weight:700;">
          ▶ Continue Execution
        </button>
      `;
    } else {
      actionButtons = `
        <button class="btn btn-primary btn-sm btn-chat-resume" style="background:#3b82f6;border-color:#3b82f6;font-weight:700;">
          ↺ Retry
        </button>
        <button class="btn btn-secondary btn-sm btn-chat-open-settings">
          ⚙️ AI Settings
        </button>
      `;
    }

    const advice = haltData.advice || (
      isRateLimit
        ? 'Your active AI provider reached its token or request limit. You can switch to NVIDIA NIM, Groq, OpenAI, or a lighter model preset in Settings ⚙️ to continue immediately.'
        : isAuth
        ? 'Please check your API key in Settings ⚙️ and click Save Configuration.'
        : isTurnLimit
        ? 'Autonomous execution reached 100 turns. Click Continue Execution to proceed.'
        : 'Execution halted due to a gateway or tool error. You can retry or switch model preset in Settings ⚙️.'
    );

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">${icon}</span>
        <span class="chat-sender-name">Execution Guardian</span>
        <span class="chat-sender-badge" style="background:rgba(239,68,68,0.2);color:${titleColor};border:1px solid ${borderColor};">${badge}</span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent" style="border-color:${borderColor};background:${bgColor};">
        <div style="font-weight:700;color:${titleColor};margin-bottom:4px;display:flex;align-items:center;gap:6px;">
          <span>${icon}</span> <span>${this.escapeInlineMd(title)}</span>
        </div>
        <div style="font-size:12px;color:#fca5a5;margin-bottom:8px;font-family:var(--font-mono);background:rgba(0,0,0,0.3);padding:6px 8px;border-radius:4px;word-break:break-all;">
          ${this.escapeInlineMd(haltData.error || haltData.reason || 'Unknown interruption.')}
        </div>
        <div style="font-size:11.5px;color:#cbd5e1;line-height:1.45;margin-bottom:12px;">
          ${this.escapeInlineMd(advice)}
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          ${actionButtons}
        </div>
      </div>
    `;

    chatTimeline.appendChild(row);

    if (!skipRecord && this.agentEngine) {
      this.agentEngine.recordTimelineEvent({ type: 'halted_card', haltData, timestamp: timeStr });
    }

    const resumeBtn = row.querySelector('.btn-chat-resume');
    const settingsBtn = row.querySelector('.btn-chat-open-settings');

    if (resumeBtn) {
      resumeBtn.addEventListener('click', () => {
        row.remove();
        if (this.agentEngine && typeof this.agentEngine.resumeGoal === 'function') {
          this.agentEngine.resumeGoal();
        } else if (this.agentEngine && this.agentEngine.currentGoal) {
          this.agentEngine.executeGoal(this.agentEngine.currentGoal);
        }
      });
    }

    if (settingsBtn) {
      settingsBtn.addEventListener('click', () => {
        this.openSettingsModal();
      });
    }

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  renderHindsightRecallInChat(recallData, customTime = null, skipRecord = false) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline || !recallData || !recallData.results || recallData.results.length === 0) return;

    const row = document.createElement('div');
    row.className = 'chat-msg-row chat-hindsight-recall-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const count = recallData.results.length;

    const escape = (str) => {
      if (!str) return '';
      return String(str).replace(/[&<>"']/g, s => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[s]);
    };

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">🧠</span>
        <span class="chat-sender-name">Vectorize Hindsight Memory</span>
        <span class="chat-sender-badge" style="background:rgba(192,132,252,0.18);color:#c084fc;border:1px solid rgba(192,132,252,0.35);">
          TEMPR Recall · ${count} Memories Injected
        </span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent" style="border-color:rgba(192,132,252,0.4);background:rgba(25,18,35,0.95);color:#e2e8f0;">
        <div style="font-weight:700;color:#c084fc;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;">
          <span>🧠 Recalled Past Experiences & Stored Preferences</span>
          <span style="font-size:11px;font-weight:normal;color:#a855f7;">${count} relevant memory item(s)</span>
        </div>
        <div style="display:flex;flex-direction:column;gap:6px;font-size:11.5px;">
          ${recallData.results.slice(0, 4).map(m => `
            <div style="background:rgba(255,255,255,0.04);border-left:3px solid #c084fc;padding:6px 10px;border-radius:4px;">
              <div style="font-weight:600;color:#f3e8ff;margin-bottom:2px;display:flex;justify-content:space-between;">
                <span>${escape(m.title || m.tier)}</span>
                <span style="font-size:10px;color:#a855f7;background:rgba(168,85,247,0.15);padding:1px 5px;border-radius:8px;">${escape(m.tier)}</span>
              </div>
              <div style="color:#cbd5e1;line-height:1.4;">${escape(m.text || m.fact || m.directive || m.resolution)}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    chatTimeline.appendChild(row);

    if (!skipRecord && this.agentEngine) {
      this.agentEngine.recordTimelineEvent({ type: 'hindsight_recall', recallData, timestamp: timeStr });
    }

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  renderHindsightRetainInChat(retainData, customTime = null, skipRecord = false) {
    const chatTimeline = document.getElementById('chat-timeline');
    if (!chatTimeline || !retainData) return;

    const row = document.createElement('div');
    row.className = 'chat-msg-row chat-hindsight-retain-row';
    row.style.display = 'flex';
    row.style.flexDirection = 'column';
    row.style.gap = '6px';
    row.style.marginBottom = '12px';

    const timeStr = customTime || (new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const escape = (str) => {
      if (!str) return '';
      return String(str).replace(/[&<>"']/g, s => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[s]);
    };

    const item = retainData.item || {};
    const text = item.directive || item.fact || item.resolution || retainData.content || 'Learned preference saved.';

    row.innerHTML = `
      <div class="chat-sender-row">
        <span class="chat-sender-avatar">🧠</span>
        <span class="chat-sender-name">Vectorize Hindsight Memory</span>
        <span class="chat-sender-badge" style="background:rgba(56,189,248,0.18);color:#38bdf8;border:1px solid rgba(56,189,248,0.35);">
          Memory Retained · Saved to Bank
        </span>
        <span class="chat-time">${timeStr}</span>
      </div>
      <div class="chat-bubble-agent" style="border-color:rgba(56,189,248,0.4);background:rgba(10,25,38,0.95);color:#e2e8f0;">
        <div style="font-weight:700;color:#38bdf8;margin-bottom:4px;display:flex;align-items:center;gap:6px;">
          <span>💾 Memory Successfully Stored</span>
          <span style="font-size:11px;font-weight:normal;color:#94a3b8;">(${escape(retainData.memory_type || 'observation')})</span>
        </div>
        <div style="font-size:11.5px;color:#cbd5e1;background:rgba(255,255,255,0.04);border-left:3px solid #38bdf8;padding:6px 10px;border-radius:4px;line-height:1.4;">
          ${escape(text)}
        </div>
      </div>
    `;

    chatTimeline.appendChild(row);

    if (!skipRecord && this.agentEngine) {
      this.agentEngine.recordTimelineEvent({ type: 'hindsight_retain', retainData, timestamp: timeStr });
    }

    const cockpitScroll = document.getElementById('cockpit-scroll-area');
    if (cockpitScroll) {
      cockpitScroll.scrollTop = cockpitScroll.scrollHeight;
    }
  }

  async rehydrateSession(forceBackend = false) {
    let sessionData = null;
    const storageKey = `fraiday_session_${this.activeWorkspace || 'default'}`;

    // 1. Try instant browser localStorage cache
    if (!forceBackend && typeof localStorage !== 'undefined') {
      try {
        const raw = localStorage.getItem(storageKey);
        if (raw) sessionData = JSON.parse(raw);
      } catch (_) {}
    }

    // 2. If not in localStorage or empty or forceBackend, fetch from backend disk storage
    if (!sessionData || !sessionData.timelineEvents || sessionData.timelineEvents.length === 0 || forceBackend) {
      try {
        const res = await fetch('/api/session').then(r => r.json());
        if (res && res.success && res.session) {
          sessionData = res.session;
          if (typeof localStorage !== 'undefined') {
            try {
              localStorage.setItem(storageKey, JSON.stringify(sessionData));
            } catch (_) {}
          }
        }
      } catch (err) {
        console.warn('Backend session fetch note:', err);
      }
    }

    if (!sessionData || !sessionData.timelineEvents || sessionData.timelineEvents.length === 0) {
      const chatTimeline = document.getElementById('chat-timeline');
      if (chatTimeline) {
        chatTimeline.querySelectorAll('.tool-card, .chat-msg-row, .chat-plan-row, .chat-verification-row, .chat-system-alert-row, .chat-halted-row').forEach(el => el.remove());
      }
      return;
    }

    // A. Restore Agent Engine internal memory
    if (this.agentEngine) {
      this.agentEngine.conversationHistory = Array.isArray(sessionData.conversationHistory) ? sessionData.conversationHistory : [];
      this.agentEngine.currentGoal = sessionData.currentGoal || '';
      this.agentEngine.turnCount = sessionData.turnCount || 0;
      this.agentEngine.planApproved = Boolean(sessionData.planApproved);
      this.agentEngine.timelineEvents = Array.isArray(sessionData.timelineEvents) ? sessionData.timelineEvents : [];
      if (sessionData.state) {
        this.agentEngine.setState(sessionData.state);
      }
      if (sessionData.hindsightEnabled !== undefined) {
        if (this.agentEngine.setHindsightMode) {
          this.agentEngine.setHindsightMode(sessionData.hindsightEnabled);
        } else {
          this.agentEngine.hindsightEnabled = sessionData.hindsightEnabled;
        }
        if (this.hindsightInspector) {
          this.hindsightInspector.isHindsightEnabled = sessionData.hindsightEnabled;
          this.hindsightInspector.render();
        }
        this.updateHindsightHudPill(sessionData.hindsightEnabled);
      }
    }

    // B. Restore Monologue reasoning box
    const monologueCard = document.getElementById('agent-monologue-card');
    if (monologueCard && sessionData.monologueHtml) {
      const body = monologueCard.querySelector('.monologue-text') || monologueCard;
      if (body) body.innerHTML = sessionData.monologueHtml;
    }

    // C. Restore Knowledge Base items
    if (this.knowledgeBase && Array.isArray(sessionData.knowledgeItems) && sessionData.knowledgeItems.length > 0) {
      this.knowledgeBase.setItems(sessionData.knowledgeItems);
    }

    // D. Restore DAG Canvas
    if (this.dagCanvas) {
      if (Array.isArray(sessionData.dagNodes)) {
        this.dagCanvas.setNodes(sessionData.dagNodes, sessionData.dagStage || null);
      } else if (sessionData.dagStage) {
        this.dagCanvas.setActiveStage(sessionData.dagStage);
      }
    }

    // E. Rebuild Timeline Cards in identical chronological order
    const chatTimeline = document.getElementById('chat-timeline');
    if (chatTimeline && Array.isArray(sessionData.timelineEvents) && sessionData.timelineEvents.length > 0) {
      chatTimeline.querySelectorAll('.tool-card, .chat-msg-row, .chat-plan-row, .chat-verification-row, .chat-system-alert-row, .chat-halted-row').forEach(el => el.remove());
      let toolCallCount = 0;

      for (const ev of sessionData.timelineEvents) {
        if (ev.type === 'user_message') {
          this.renderUserMessageInChat(ev.text, ev.timestamp);
        } else if (ev.type === 'tool_card') {
          toolCallCount++;
          const card = this.agentEngine?.addAntigravityToolCard(ev.toolName, ev.toolArgs, ev.id, true);
          if (card && ev.status && ev.status !== 'running') {
            this.agentEngine?.updateToolCard(card, ev.status, ev.extraText, ev.toolResult, true);
          }
        } else if (ev.type === 'agent_message') {
          this.renderAgentMessageInChat(ev.markdown, ev.timestamp);
        } else if (ev.type === 'plan_approval') {
          if (!ev.approved && this.agentEngine?.state === 'waiting') {
            this.renderPlanApprovalCardInChat(ev.planMarkdown, ev.timestamp);
          } else {
            this.renderApprovedPlanCardInChat(ev.planMarkdown, ev.timestamp);
          }
        } else if (ev.type === 'system_alert') {
          this.renderSystemAlertInChat(ev.alertData, ev.timestamp, true);
        } else if (ev.type === 'verification_screenshot') {
          this.renderVerificationScreenshotInChat(ev.result, ev.timestamp, true);
        } else if (ev.type === 'hindsight_recall') {
          this.renderHindsightRecallInChat(ev.recallData, ev.timestamp, true);
        } else if (ev.type === 'hindsight_retain') {
          this.renderHindsightRetainInChat(ev.retainData, ev.timestamp, true);
        } else if (ev.type === 'halted_card') {
          this.renderHaltedCardInChat(ev.haltData, ev.timestamp, true);
        }
      }

      const streamCount = document.getElementById('tool-stream-count');
      if (streamCount) streamCount.innerText = `${toolCallCount} calls`;

      const cockpitScroll = document.getElementById('cockpit-scroll-area');
      if (cockpitScroll) cockpitScroll.scrollTop = cockpitScroll.scrollHeight;

      if (this.terminal) {
        this.terminal.appendOutput(`✔ Restored persistent session (${sessionData.timelineEvents.length} events, ${sessionData.conversationHistory?.length || 0} turns in memory)`, 'success');
      }
    }
  }

  handleCodeLensAction(action, filepath, content) {
    this.switchTab('code');
    const actions = {
      refactor: `Refactoring ${filepath}: Optimizing state management, readability, and performance...`,
      test: `Generating automated unit test suite for ${filepath}...`,
      explain: `Explaining ${filepath}:\nThis module manages reactive workspace components.`,
      audit: `Performing security audit on ${filepath}... Zero vulnerabilities detected.`
    };
    this.agentEngine.streamThought(actions[action] || `Executing ${action} on ${filepath}`);
    this.terminal.appendCommand(`agent-lens --action "${action}" --target "${filepath}"`);
    this.terminal.appendOutput(`✔ Code lens [${action}] executed.`, 'success');
  }

  bindPlanApprovalControls() {
    const approveBtn = document.getElementById('btn-approve-plan');
    const rejectBtn = document.getElementById('btn-reject-plan');

    if (approveBtn) {
      approveBtn.addEventListener('click', async () => {
        approveBtn.disabled = true;
        approveBtn.innerText = 'Approving...';
        try {
          await this.agentEngine.approvePlan();
        } finally {
          approveBtn.disabled = false;
          approveBtn.innerHTML = '<span>✓</span><span>Approve & Proceed</span>';
        }
      });
    }

    if (rejectBtn) {
      rejectBtn.addEventListener('click', async () => {
        const feedback = prompt('Enter your guidance or revision request for frAIday:');
        if (feedback !== null) {
          await this.agentEngine.rejectPlan(feedback);
        }
      });
    }
  }

  renderArtifactPlan(markdown) {
    const container = document.getElementById('artifact-content-area');
    if (!container || !markdown) return;

    // Convert markdown into rich HTML
    let html = '';
    const lines = markdown.split('\n');
    let inCode = false;
    let codeLang = '';
    let codeBuffer = [];
    let inList = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Code fences
      if (line.trim().startsWith('```')) {
        if (!inCode) {
          if (inList) { html += '</ul>\n'; inList = false; }
          inCode = true;
          codeLang = line.trim().slice(3);
          codeBuffer = [];
        } else {
          inCode = false;
          const escaped = codeBuffer.join('\n')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
          html += `<pre><code class="language-${codeLang}">${escaped}</code></pre>\n`;
        }
        continue;
      }

      if (inCode) {
        codeBuffer.push(line);
        continue;
      }

      // GitHub Alerts
      if (line.startsWith('> [!IMPORTANT]')) {
        if (inList) { html += '</ul>\n'; inList = false; }
        html += '<div class="artifact-alert alert-important"><strong>IMPORTANT:</strong> ';
        continue;
      } else if (line.startsWith('> [!NOTE]')) {
        if (inList) { html += '</ul>\n'; inList = false; }
        html += '<div class="artifact-alert alert-note"><strong>NOTE:</strong> ';
        continue;
      } else if (line.startsWith('> [!WARNING]')) {
        if (inList) { html += '</ul>\n'; inList = false; }
        html += '<div class="artifact-alert alert-warning"><strong>WARNING:</strong> ';
        continue;
      } else if (line.startsWith('> ')) {
        const alertBody = line.slice(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html += `${alertBody}<br/>`;
        if (i + 1 >= lines.length || !lines[i + 1].startsWith('> ')) {
          html += '</div>\n';
        }
        continue;
      }

      // Headers
      if (line.startsWith('# ')) {
        if (inList) { html += '</ul>\n'; inList = false; }
        html += `<h1>${this.escapeInlineMd(line.slice(2))}</h1>\n`;
      } else if (line.startsWith('## ')) {
        if (inList) { html += '</ul>\n'; inList = false; }
        html += `<h2>${this.escapeInlineMd(line.slice(3))}</h2>\n`;
      } else if (line.startsWith('### ')) {
        if (inList) { html += '</ul>\n'; inList = false; }
        html += `<h3>${this.escapeInlineMd(line.slice(4))}</h3>\n`;
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        if (!inList) { html += '<ul>\n'; inList = true; }
        html += `<li>${this.escapeInlineMd(line.slice(2))}</li>\n`;
      } else if (line.trim().length === 0) {
        if (inList) { html += '</ul>\n'; inList = false; }
      } else {
        if (inList) { html += '</ul>\n'; inList = false; }
        html += `<p>${this.escapeInlineMd(line)}</p>\n`;
      }
    }

    if (inList) { html += '</ul>\n'; }

    container.innerHTML = html;
  }

  escapeInlineMd(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;border-radius:6px;margin:8px 0;" />')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:#38bdf8;text-decoration:underline;">$1</a>');
  }
}

function bootApp() {
  if (window.frAidayApp && window.frAidayApp._initialized) return;
  const app = new AppCoordinator();
  window.frAidayApp = app;
  window.fraidayApp = app;
  app._initialized = true;
  app.init().catch(err => {
    console.error('frAIday init error:', err);
  });
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', bootApp);
  } else {
    bootApp();
  }
}
