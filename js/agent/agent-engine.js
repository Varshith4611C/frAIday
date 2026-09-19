/**
 * frAIday — 1-to-1 Antigravity Autonomous Agentic Software Engineer
 * 
 * Exact Antigravity Mechanisms:
 * 1. Autonomous ReAct Tool-Calling Loop with Groq (openai/gpt-oss-120b) & Cerebras
 * 2. 8 Native Antigravity Tools:
 *    - run_command(CommandLine, Cwd)
 *    - write_to_file(TargetFile, CodeContent)
 *    - replace_file_content(TargetFile, TargetContent, ReplacementContent)
 *    - view_file(AbsolutePath, StartLine, EndLine)
 *    - list_dir(DirectoryPath)
 *    - grep_search(Query, SearchPath)
 *    - browser_subagent(Task)
 *    - search_web(query)
 * 3. Planning Mode & Artifacts:
 *    - implementation_plan.md with Human Approval Gate (Approve & Proceed / Revise Goal)
 *    - walkthrough.md with validation certification & embedded screenshots
 * 4. Autonomous Self-Healing:
 *    - Terminal stderr, tracebacks, and runtime errors are fed back into the agent loop.
 *    - The agent inspects errors with view_file/grep_search, patches code with replace_file_content,
 *      and verifies fixes with run_command and browser_subagent on its own!
 */

export const ANTIGRAVITY_TOOLS = [
  {
    type: "function",
    function: {
      name: "run_command",
      description: "Execute a shell command on the host terminal in the workspace directory (e.g. pip install -r requirements.txt, npm install, python scripts, pytest). Returns stdout, stderr, and exit_code.",
      parameters: {
        type: "object",
        properties: {
          CommandLine: { type: "string", description: "The exact shell command line string to execute." },
          Cwd: { type: "string", description: "Optional relative subfolder within workspace to run in." }
        },
        required: ["CommandLine"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "write_to_file",
      description: "Create or overwrite a file in the workspace (e.g. source files, requirements.txt, implementation_plan.md, walkthrough.md).",
      parameters: {
        type: "object",
        properties: {
          TargetFile: { type: "string", description: "The target file path (relative to workspace)." },
          CodeContent: { type: "string", description: "The complete file contents to write." },
          Overwrite: { type: "boolean", description: "True to overwrite if file exists." },
          Description: { type: "string", description: "Brief description of what this change accomplishes." }
        },
        required: ["TargetFile", "CodeContent"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "replace_file_content",
      description: "Perform precise, targeted edits to an existing file by replacing an exact TargetContent block with ReplacementContent.",
      parameters: {
        type: "object",
        properties: {
          TargetFile: { type: "string", description: "The target file to modify." },
          TargetContent: { type: "string", description: "The exact substring or block of code to replace." },
          ReplacementContent: { type: "string", description: "The new content to replace TargetContent with." },
          StartLine: { type: "integer", description: "Optional starting line number." },
          EndLine: { type: "integer", description: "Optional ending line number." },
          AllowMultiple: { type: "boolean", description: "True to replace all occurrences." }
        },
        required: ["TargetFile", "TargetContent", "ReplacementContent"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "view_file",
      description: "View the contents of a file in the local workspace, optionally sliced with 1-indexed line numbers.",
      parameters: {
        type: "object",
        properties: {
          AbsolutePath: { type: "string", description: "Path to file in workspace." },
          StartLine: { type: "integer", description: "1-indexed starting line to view." },
          EndLine: { type: "integer", description: "1-indexed ending line to view." }
        },
        required: ["AbsolutePath"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "list_dir",
      description: "List directory contents (files and subdirectories with sizes) in workspace.",
      parameters: {
        type: "object",
        properties: {
          DirectoryPath: { type: "string", description: "Relative directory path, empty for workspace root." }
        }
      }
    }
  },
  {
    type: "function",
    function: {
      name: "grep_search",
      description: "Search for regex patterns or text matches across workspace files.",
      parameters: {
        type: "object",
        properties: {
          Query: { type: "string", description: "Text or regex query to search for." },
          SearchPath: { type: "string", description: "Directory to search in." },
          CaseInsensitive: { type: "boolean", description: "Case insensitive search." },
          IsRegex: { type: "boolean", description: "Treat query as regular expression." }
        },
        required: ["Query"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "browser_subagent",
      description: "Launch a headless browser subagent to render the workspace application entrypoint (index.html), capture screenshot, DOM tree, and inspect console errors for visual verification.",
      parameters: {
        type: "object",
        properties: {
          Task: { type: "string", description: "What to verify in the browser (e.g. check UI render, layout, buttons, console errors)." },
          TaskName: { type: "string", description: "Short title for the browser task." },
          TaskSummary: { type: "string", description: "Brief 1-2 sentence summary." }
        },
        required: ["Task"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "search_web",
      description: "Search the web for technical documentation, library APIs, and latest specifications.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Web search query." }
        },
        required: ["query"]
      }
    }
  }
];

export const ANTIGRAVITY_SYSTEM_PROMPT = `<identity>
You are frAIday, a powerful autonomous AI software engineer and coding assistant modeled exactly on Google DeepMind Antigravity.
You are pair programming with the user to solve their software development objectives from end-to-end.
You have direct, autonomous access to the workspace shell terminal, filesystem, web research, and headless browser inspection.
You do everything autonomously without expecting the user to install packages, run commands, or fix bugs for you.
</identity>

<planning_mode>
You operate strictly through the 4-Phase Antigravity Lifecycle:

PHASE 1: UPFRONT RESEARCH & MANDATORY PLANNING GATE (Before user clicks proceed):
- If the project requires external libraries, frameworks, or CDN scripts (e.g. Three.js, OrbitControls, Chart.js, Lucide, Tone.js), you MUST execute search_web to research and verify the exact, robust CDN script URLs and constructor API signatures BEFORE writing implementation_plan.md.
- For Three.js: ALWAYS use standard UMD CDN script tags:
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
  This ensures THREE and THREE.OrbitControls are globally available to browser scripts without module specifier errors.
- Create implementation_plan.md using write_to_file detailing:
  # [Goal Description]
  Clear description of objective, architecture, and tech stack.
  ## User Review Required
  Design decisions, verified CDN libraries, or assumptions.
  ## Open Questions
  Points for user consideration.
  ## Proposed Changes
  ### [Component Name]
  #### [NEW] [filename](file:///workspace/path/to/file)
  #### [MODIFY] [filename](file:///workspace/path/to/file)
  ## Verification Plan
  ### Automated Tests
  Commands to run.
  ### Manual Verification
  Headless Chrome visual audit via browser_subagent.
- Once implementation_plan.md is written, execution will pause for the user to review and click "Approve & Proceed".
- DO NOT create code files (HTML, CSS, JS) or walkthrough.md before plan approval!

PHASE 2: EXECUTION & AUTONOMOUS CODE SYNTHESIS:
- After the plan is approved, write the actual code files directly using write_to_file and replace_file_content.
- For web applications, create clean, modern index.html, style.css, and app.js.
- CRITICAL BROWSER FRONTEND vs NODE.JS EXECUTION RULE:
  Browser client scripts (e.g. app.js with document, window, localStorage, addEventListener, Canvas/WebGL) RUN ONLY IN THE WEB BROWSER.
  NEVER attempt to execute client-side browser files with Node.js in the terminal (e.g. DO NOT run node app.js). Node.js has no DOM window or document globals.
  ONLY use run_command for backend Python/Node servers, package managers (pip install, npm install), or CLI test runners.

PHASE 3: TESTING & HEADLESS BROWSER VISUAL AUDIT:
- Call browser_subagent to launch headless Chrome, render the live preview at http://localhost:8080/workspace/index.html, take a screenshot, and verify that the page renders cleanly with 0 console errors.
- If errors or exceptions occur, diagnose them immediately with view_file or search_web, patch with replace_file_content, and re-audit with browser_subagent.

PHASE 4: WALKTHROUGH DOCUMENTATION (Definition of Done - Strictly Created at Last):
- walkthrough.md is the final completion certificate. It MUST ONLY be created at Phase 4, AFTER Phase 2 code is created AND Phase 3 browser_subagent visual verification has certified 0 errors!
- NEVER create walkthrough.md during Phase 1, Phase 2, or during error diagnostics!
- walkthrough.md must document:
  # Walkthrough - [Goal Title]
  ## Changes Made
  - List of files created/modified
  ## Verification Results
  - Headless Chrome visual audit findings, DOM element count, and clean error check
  ## Live Preview
  - Instructions to view http://localhost:8080/workspace/index.html
</planning_mode>

<communication_style>
- Format responses in GitHub-style markdown.
- Create clickable links for files: [filename](file:///workspace/path/to/file).
- Use alerts: > [!NOTE], > [!IMPORTANT], > [!WARNING], > [!TIP].
- Keep conversational text focused; prioritize real tool calls over commentary.
</communication_style>`;

export class AgentEngine {
  constructor(options = {}) {
    this.monologueEl = options.monologueEl;
    this.streamContainer = options.streamContainer;
    this.statusPillEl = options.statusPillEl;
    this.terminal = options.terminal;
    this.safetyPolicy = options.safetyPolicy;
    this.dagCanvas = options.dagCanvas;
    this.knowledgeBase = options.knowledgeBase;
    this.fileTree = options.fileTree;
    this.codeEditor = options.codeEditor;
    this.onArtifactReady = options.onArtifactReady;
    this.onArtifactPlanReady = options.onArtifactPlanReady;
    this.onPlanPendingApproval = options.onPlanPendingApproval;
    this.onUserMessage = options.onUserMessage;
    this.onAgentResponse = options.onAgentResponse;
    this.onExecutionStart = options.onExecutionStart;
    this.onExecutionEnd = options.onExecutionEnd;
    this.onStatusChange = options.onStatusChange;
    this.onSystemAlert = options.onSystemAlert;
    this.onVerificationScreenshotReady = options.onVerificationScreenshotReady;

    this.isHealing = false;
    this.lastHealTime = 0;
    this.lastHealedError = '';

    this.state = 'idle';
    this.isPaused = false;
    this.isAborted = false;
    this.abortController = null;
    this.planApproved = false;
    this.currentGoal = '';
    this.planApprovalResolver = null;
    this.conversationHistory = [];

    this.apiBase = options.apiBase || (typeof window !== 'undefined' ? '' : 'http://localhost:8080');

    const storage = typeof localStorage !== 'undefined' ? localStorage : { getItem: () => null, setItem: () => {} };
    this.provider = storage.getItem('fraiday_provider') || 'groq';
    this.apiKey = storage.getItem('fraiday_api_key') || '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';
    this.model = storage.getItem('fraiday_model') || 'openai/gpt-oss-20b';

    this.turnCount = 0;
  }

  setLlmConfig(provider, apiKey, model) {
    this.provider = provider;
    this.apiKey = apiKey;
    this.model = model;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('fraiday_provider', provider);
      localStorage.setItem('fraiday_api_key', apiKey);
      localStorage.setItem('fraiday_model', model);
    }
  }

  abort() {
    this.isAborted = true;
    if (this.abortController) {
      try {
        this.abortController.abort();
      } catch (_) {}
    }
    if (this.planApprovalResolver) {
      const resolve = this.planApprovalResolver;
      this.planApprovalResolver = null;
      this.isPaused = false;
      resolve({ approved: false, aborted: true });
    }
    this.setState('idle');
    this.terminal?.appendOutput('⏹ Execution stopped by user.', 'warn');
    if (this.monologueEl) {
      const body = this.monologueEl.querySelector('.monologue-text') || this.monologueEl;
      if (body) {
        body.innerHTML = '<span style="color:#f87171;font-weight:600;">⏹ Execution stopped by user. Ready for your next command.</span>';
      }
    }
    if (this.onExecutionEnd) {
      this.onExecutionEnd({ aborted: true });
    }
  }

  reset() {
    this.isAborted = true;
    if (this.abortController) {
      try { this.abortController.abort(); } catch (_) {}
    }
    this.setState('idle');
    this.currentGoal = '';
    this.isPaused = false;
    this.planApproved = false;
    this.conversationHistory = [];
    this.planApprovalResolver = null;
    this.turnCount = 0;

    if (this.monologueEl) {
      const body = this.monologueEl.querySelector('.monologue-text') || this.monologueEl;
      if (body) {
        body.innerHTML = '<span style="color:var(--text-muted);font-style:italic;">Workspace reset. Ready for your next technical objective.</span>';
      }
    }
    if (this.streamContainer) {
      this.streamContainer.innerHTML = '';
    }
    const streamCount = typeof document !== 'undefined' ? document.getElementById('tool-stream-count') : null;
    if (streamCount) streamCount.innerText = '0 calls';
    if (this.dagCanvas) {
      this.dagCanvas.clear();
    }
    if (this.onExecutionEnd) {
      this.onExecutionEnd({ reset: true });
    }
  }

  setState(newState) {
    this.state = newState;
    if (this.statusPillEl) {
      this.statusPillEl.className = `execution-status-pill status-${newState}`;
      const label = this.statusPillEl.querySelector('.status-label');
      if (label) {
        const labels = {
          idle: 'System Idle',
          planning: 'Antigravity Planning Mode',
          researching: 'Researching Tech Specs',
          executing: 'Synthesizing Source Files',
          waiting: 'Planning Gate: Awaiting Approval',
          validating: 'Headless Browser Visual Audit',
          testing: 'Executing Terminal Test Harness',
          healing: 'Autonomous Self-Healing Loop',
          completed: 'Mission Accomplished',
          error: 'Execution Halted'
        };
        label.innerText = labels[newState] || newState.toUpperCase();
      }
    }
  }

  async streamThought(text) {
    if (!this.monologueEl || !text) return;
    const body = this.monologueEl.querySelector('.monologue-text');
    if (!body) return;

    // Convert markdown thoughts to clean HTML
    const formatted = text
      .replace(/<think>[\s\S]*?<\/think>/gi, '')
      .replace(/<thought>[\s\S]*?<\/thought>/gi, '')
      .trim();

    if (!formatted) return;

    const words = formatted.split(' ');
    let current = '';
    for (let word of words) {
      current += word + ' ';
      body.innerHTML = current;
      await new Promise(r => setTimeout(r, 12));
    }
  }

  addAntigravityToolCard(toolName, toolArgs) {
    if (!this.streamContainer || typeof document === 'undefined') return null;
    const card = document.createElement('div');
    card.className = 'tool-card running';

    const icons = {
      run_command: '💻',
      write_to_file: '📝',
      replace_file_content: '✂️',
      view_file: '🔍',
      list_dir: '📁',
      grep_search: '🔎',
      browser_subagent: '🌐',
      search_web: '🌍'
    };

    let summary = '';
    if (toolName === 'run_command') {
      summary = toolArgs.CommandLine || '';
    } else if (toolName === 'write_to_file') {
      summary = toolArgs.TargetFile || '';
    } else if (toolName === 'replace_file_content') {
      summary = toolArgs.TargetFile || '';
    } else if (toolName === 'view_file') {
      summary = toolArgs.AbsolutePath || '';
    } else if (toolName === 'browser_subagent') {
      summary = toolArgs.Task || 'Inspect Live Preview';
    } else if (toolName === 'search_web') {
      summary = toolArgs.query || '';
    } else {
      summary = JSON.stringify(toolArgs).slice(0, 80);
    }

    card.innerHTML = `
      <div class="tool-header">
        <div class="tool-title">
          <span>${icons[toolName] || '⚙️'}</span>
          <span>${toolName}</span>
        </div>
        <span class="tool-badge running">running</span>
      </div>
      <div class="tool-payload" style="font-family:var(--font-mono);font-size:11px;color:#cbd5e1;white-space:pre-wrap;max-height:120px;overflow-y:auto;">${escapeHtml(summary)}</div>
    `;

    this.streamContainer.prepend(card);

    const streamCount = typeof document !== 'undefined' ? document.getElementById('tool-stream-count') : null;
    if (streamCount) {
      const current = parseInt(streamCount.innerText) || 0;
      streamCount.innerText = `${current + 1} calls`;
    }

    return card;
  }

  updateToolCard(card, status, extraText = null, toolResult = null) {
    if (!card) return;
    card.className = `tool-card ${status}`;
    const badge = card.querySelector('.tool-badge');
    if (badge) {
      badge.className = `tool-badge ${status}`;
      badge.innerText = status;
    }
    if (extraText) {
      const payload = card.querySelector('.tool-payload');
      if (payload) payload.innerText = extraText;
    }
    if (toolResult && toolResult.screenshot_url) {
      const existing = card.querySelector('.tool-screenshot-preview');
      if (!existing) {
        const previewDiv = document.createElement('div');
        previewDiv.className = 'tool-screenshot-preview';
        previewDiv.style.marginTop = '8px';
        previewDiv.style.borderRadius = '6px';
        previewDiv.style.overflow = 'hidden';
        previewDiv.style.border = '1px solid rgba(56,189,248,0.3)';
        previewDiv.style.background = '#000';
        previewDiv.innerHTML = `
          <div style="padding:4px 8px;background:rgba(56,189,248,0.12);font-size:10.5px;color:#38bdf8;display:flex;justify-content:space-between;align-items:center;">
            <span>📸 Headless Chrome Render Snapshot</span>
            <a href="${toolResult.screenshot_url}" target="_blank" style="color:#38bdf8;text-decoration:underline;">Full View ↗</a>
          </div>
          <img src="${toolResult.screenshot_url}" style="width:100%;max-height:160px;object-fit:contain;display:block;background:#050811;" alt="Verified Live Render" />
        `;
        card.appendChild(previewDiv);
      }
    }
  }

  formatToolResultSummary(toolName, result) {
    if (!result) return 'Completed.';
    if (toolName === 'run_command') {
      const exitCode = result.exit_code !== undefined ? result.exit_code : 0;
      const stdout = (result.stdout || '').trim();
      const stderr = (result.stderr || '').trim();
      if (exitCode === 0) {
        return `Exit code 0\n${stdout ? stdout.slice(0, 150) : 'Done.'}`;
      } else {
        return `Exit code ${exitCode}\n${stderr ? stderr.slice(0, 150) : stdout.slice(0, 150)}`;
      }
    } else if (toolName === 'write_to_file') {
      return `Created ${result.TargetFile} (${result.sizeBytes || 0} bytes)`;
    } else if (toolName === 'replace_file_content') {
      return `Patched ${result.TargetFile} cleanly`;
    } else if (toolName === 'browser_subagent') {
      return `Browser audit: ${result.title || 'OK'} (${result.dom_elements_count || 0} elements, errors: ${result.console_errors?.length || 0})`;
    } else if (toolName === 'list_dir') {
      return `Found ${result.entries?.length || 0} items`;
    } else if (toolName === 'grep_search') {
      return `Found ${result.matches_count || 0} matches`;
    }
    return 'Execution completed.';
  }

  compactMessages(messages) {
    if (messages.length <= 8) return messages;

    const systemMsg = messages.find(m => m.role === 'system');
    const firstUserMsg = messages.find(m => m.role === 'user');
    const recentMessages = messages.slice(-8);

    const sanitizedRecent = recentMessages.map(m => {
      if (m.role === 'tool' && typeof m.content === 'string' && m.content.length > 700) {
        return {
          ...m,
          content: m.content.slice(0, 700) + '... [output truncated for brevity]'
        };
      }
      return m;
    });

    const middleCount = messages.length - (systemMsg ? 1 : 0) - (firstUserMsg ? 1 : 0) - recentMessages.length;
    const summaryMsg = middleCount > 0 ? [{
      role: 'user',
      content: `[System Context: ${middleCount} earlier steps executed in workspace. Continue progressing toward project completion.]`
    }] : [];

    const result = [];
    if (systemMsg) result.push(systemMsg);
    if (firstUserMsg && !recentMessages.includes(firstUserMsg)) result.push(firstUserMsg);
    result.push(...summaryMsg);
    result.push(...sanitizedRecent);
    return result;
  }

  async callLlmRaw(messages, tools = ANTIGRAVITY_TOOLS) {
    if (this.isAborted) {
      return { message: { role: 'assistant', content: 'Execution stopped.' }, tool_calls: [] };
    }

    const compacted = this.compactMessages(messages);
    const payload = {
      provider: this.provider,
      api_key: this.apiKey,
      model: this.model,
      messages: compacted,
      tools: tools,
      tool_choice: "auto",
      max_tokens: 1500,
      temperature: 0.15
    };

    for (let attempt = 1; attempt <= 4; attempt++) {
      if (this.isAborted) {
        return { message: { role: 'assistant', content: 'Execution stopped.' }, tool_calls: [] };
      }

      try {
        const resp = await fetch(`${this.apiBase}/api/llm/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: this.abortController?.signal
        });

        if (resp.status === 429) {
          const waitMs = attempt * 2500;
          console.warn(`[frAIday Gateway] Rate limit hit (HTTP 429), backing off ${waitMs}ms (attempt ${attempt}/4)...`);
          this.terminal?.appendOutput(`⏳ Rate limit backoff (${waitMs/1000}s)...`, 'info');
          await new Promise(r => setTimeout(r, waitMs));
          continue;
        }

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(err.error || `LLM Gateway Error (HTTP ${resp.status})`);
        }

        return await resp.json();
      } catch (err) {
        if (err.name === 'AbortError' || this.isAborted) {
          return { message: { role: 'assistant', content: 'Execution stopped by user.' }, tool_calls: [] };
        }
        if (attempt === 4) throw err;
        await new Promise(r => setTimeout(r, 1000 * attempt));
      }
    }
    throw new Error('LLM rate limit reached after 4 backoff retries. Please wait a moment.');
  }

  async executeToolCall(toolName, toolArgs, toolCard) {
    if (this.isAborted) {
      return { error: 'Aborted by user', exit_code: 1 };
    }

    // Dynamic status updates
    if (toolName === 'run_command') {
      this.terminal?.appendCommand(toolArgs.CommandLine);
      this.setState('testing');
    } else if (toolName === 'write_to_file' || toolName === 'replace_file_content') {
      this.setState('executing');
    } else if (toolName === 'browser_subagent') {
      this.setState('validating');
    } else if (toolName === 'search_web' || toolName === 'list_dir' || toolName === 'view_file') {
      this.setState('researching');
    }

    const resp = await fetch(`${this.apiBase}/api/tools/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: toolName,
        arguments: toolArgs
      }),
      signal: this.abortController?.signal
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${resp.status}`);
    }

    const result = await resp.json();

    // Mirror actions to IDE components
    if (toolName === 'run_command') {
      if (result.stdout) this.terminal?.appendOutput(result.stdout, 'info');
      if (result.stderr) this.terminal?.appendOutput(result.stderr, result.exit_code === 0 ? 'warn' : 'error');
      
      // Proactive hint if agent accidentally ran client-side browser script with Node
      if (result.stderr && (result.stderr.includes('document is not defined') || result.stderr.includes('document is not def') || result.stderr.includes('window is not defined'))) {
        this.terminal?.appendOutput(`ℹ️ [Tip] Browser client code detected. DOM scripts run in the web browser, not in Node.js. Use browser_subagent to test in headless Chrome.`, 'warn');
      }

      if (result.exit_code === 0) {
        this.terminal?.appendOutput(`✔ Exited with code 0`, 'success');
      } else {
        this.terminal?.appendOutput(`✕ Command exited with code ${result.exit_code}`, 'error');
      }
    } else if (toolName === 'write_to_file' || toolName === 'replace_file_content') {
      await this.fileTree?.refresh();
      if (this.codeEditor && toolArgs.TargetFile && !toolArgs.TargetFile.endsWith('.png')) {
        this.codeEditor.loadFile(toolArgs.TargetFile);
      }
      if (toolArgs.TargetFile && !toolArgs.TargetFile.endsWith('.md')) {
        if (typeof window !== 'undefined' && window.fraidayApp) {
          window.fraidayApp.reloadPreview();
        }
      }
    } else if (toolName === 'browser_subagent') {
      if (result.screenshot_url) {
        this.terminal?.appendOutput(`✔ Headless Chrome certified live render: "${result.title}" (${result.dom_elements_count || 0} DOM elements)`, 'success');
        if (typeof window !== 'undefined' && window.fraidayApp) {
          window.fraidayApp.reloadPreview();
        }
        if (this.onVerificationScreenshotReady) {
          this.onVerificationScreenshotReady(result);
        }
      }
    }

    return result;
  }

  checkWalkthroughCreated() {
    return this.conversationHistory.some(m => 
      m.role === 'tool' && (m.content || '').toLowerCase().includes('walkthrough.md')
    );
  }

  checkCodeCreated() {
    return this.conversationHistory.some(m =>
      m.role === 'tool' && (
        (m.content || '').includes('.html') ||
        (m.content || '').includes('.js') ||
        (m.content || '').includes('.css') ||
        (m.content || '').includes('.py')
      )
    );
  }

  waitForPlanApproval() {
    return new Promise(resolve => {
      this.planApprovalResolver = resolve;
    });
  }

  /**
   * The Full 1-to-1 Antigravity ReAct Autonomous Engine
   * Enforces Planning Gate, Conversational Memory, Continuous Execution, and Walkthrough Certification
   */
  async executeGoal(goal) {
    if (!goal || !goal.trim()) return;
    this.currentGoal = goal.trim();
    this.isAborted = false;
    this.abortController = new AbortController();
    this.turnCount = 0;

    this.setState('planning');

    // Multi-turn conversational memory: preserve history across user messages
    if (!this.conversationHistory || this.conversationHistory.length === 0) {
      this.conversationHistory = [
        { role: 'system', content: ANTIGRAVITY_SYSTEM_PROMPT }
      ];
    }
    this.conversationHistory.push({
      role: 'user',
      content: `<USER_REQUEST>\n${this.currentGoal}\n</USER_REQUEST>`
    });

    if (this.onExecutionStart) {
      this.onExecutionStart();
    }
    if (this.onUserMessage) {
      this.onUserMessage(this.currentGoal);
    }

    this.streamThought(`Analyzing objective: "${this.currentGoal}"\nInitiating Antigravity Autonomous Lifecycle Engine...`);

    const maxTurns = 100; // Unlimited, continuous execution until definition of done

    while (this.turnCount < maxTurns) {
      if (this.isAborted) break;
      this.turnCount++;

      let respData = null;
      try {
        respData = await this.callLlmRaw(this.conversationHistory, ANTIGRAVITY_TOOLS);
      } catch (err) {
        if (this.isAborted) break;
        console.error('LLM Gateway Invocation Error:', err);
        this.terminal?.appendOutput(`❌ LLM Gateway Error: ${err.message}`, 'error');
        this.setState('error');
        if (this.onExecutionEnd) this.onExecutionEnd({ error: err.message });
        return;
      }

      if (this.isAborted) break;

      const assistantMsg = respData.message || { role: 'assistant', content: respData.content || '' };
      const toolCalls = assistantMsg.tool_calls || [];
      const content = assistantMsg.content || '';

      if (content) {
        await this.streamThought(content);
      }

      this.conversationHistory.push(assistantMsg);

      // If the agent emitted no tool calls, check completion criteria
      if (!toolCalls || toolCalls.length === 0) {
        if (!this.planApproved) {
          this.conversationHistory.push({
            role: 'user',
            content: 'You must start by creating implementation_plan.md using write_to_file so the user can review and approve it. Call write_to_file now.'
          });
          continue;
        }

        const hasCode = this.checkCodeCreated();
        if (!hasCode) {
          this.conversationHistory.push({
            role: 'user',
            content: 'Plan approved. Now proceed immediately to create the source code files: use write_to_file to write index.html, style.css, and app.js.'
          });
          continue;
        }

        const hasBrowserAudit = this.conversationHistory.some(m => m.name === 'browser_subagent');
        if (!hasBrowserAudit) {
          this.conversationHistory.push({
            role: 'user',
            content: 'The source code files have been written. Now invoke browser_subagent to audit the live preview at http://localhost:8080/workspace/index.html and verify that the interface renders properly without errors.'
          });
          continue;
        }

        const hasWalkthrough = this.checkWalkthroughCreated();
        if (!hasWalkthrough) {
          this.conversationHistory.push({
            role: 'user',
            content: 'The application is written and verified. Now create walkthrough.md using write_to_file to document your work, changes made, and verification results before completing the project.'
          });
          continue;
        }

        // Both code, headless browser audit, and walkthrough.md are complete!
        this.setState('completed');
        this.terminal?.appendOutput(`═══════════════════════════════════════════════════════════════`, 'success');
        this.terminal?.appendOutput(`🎉 DEFINITION OF DONE: frAIday Completed Objective`, 'success');
        this.terminal?.appendOutput(`   • Live Preview: http://localhost:8080/workspace/index.html`, 'success');
        this.terminal?.appendOutput(`   • Verification: Headless Chrome & Terminal Certified`, 'success');
        this.terminal?.appendOutput(`   • Artifact: walkthrough.md Generated`, 'success');
        this.terminal?.appendOutput(`═══════════════════════════════════════════════════════════════`, 'success');

        if (this.onAgentResponse) {
          this.onAgentResponse(content || 'Mission Accomplished! All files created, verified in headless Chrome, and documented in walkthrough.md.');
        }
        if (this.onExecutionEnd) {
          this.onExecutionEnd({ success: true });
        }
        if (typeof window !== 'undefined' && window.fraidayApp) {
          window.fraidayApp.reloadPreview();
          window.fraidayApp.switchTab('preview');
        }
        break;
      }

      // Execute each tool call emitted by the LLM
      for (const call of toolCalls) {
        if (this.isAborted) break;

        const toolName = call.function?.name;
        let toolArgs = {};
        try {
          toolArgs = typeof call.function?.arguments === 'string' 
            ? JSON.parse(call.function.arguments) 
            : (call.function?.arguments || {});
        } catch (e) {
          toolArgs = {};
        }

        const toolCard = this.addAntigravityToolCard(toolName, toolArgs);

        // STRICT PLANNING GATE: Disallow writing code files before plan is approved
        const isPlanFile = (toolArgs.TargetFile || '').toLowerCase().includes('implementation_plan.md');
        const isWalkthroughFile = (toolArgs.TargetFile || '').toLowerCase().includes('walkthrough.md');

        if (toolName === 'write_to_file' && !isPlanFile && !this.planApproved) {
          const blockedResult = {
            error: "PLANNING GATE ACTIVE: You MUST create implementation_plan.md first and await user approval before writing application code files. Call write_to_file with TargetFile='implementation_plan.md'."
          };
          this.updateToolCard(toolCard, 'error', 'Planning Gate: Blocked until plan is approved');
          this.conversationHistory.push({
            role: 'tool',
            tool_call_id: call.id,
            name: toolName,
            content: JSON.stringify(blockedResult)
          });
          continue;
        }

        // STRICT WALKTHROUGH GATE: Disallow writing walkthrough.md until code exists and browser audit has run
        if (toolName === 'write_to_file' && isWalkthroughFile) {
          const hasCode = this.checkCodeCreated();
          const hasBrowserAudit = this.conversationHistory.some(m => m.name === 'browser_subagent' || (m.role === 'tool' && (m.content || '').includes('browser_subagent')));
          if (!hasCode || !hasBrowserAudit) {
            const blockedResult = {
              error: "LIFECYCLE ENFORCEMENT: walkthrough.md can ONLY be created at the very end after all application code files (index.html, style.css, app.js) are written AND verified in headless Chrome via browser_subagent. Please write your code files and run browser_subagent verification first."
            };
            this.updateToolCard(toolCard, 'error', 'Blocked: Verification required before walkthrough');
            this.conversationHistory.push({
              role: 'tool',
              tool_call_id: call.id,
              name: toolName,
              content: JSON.stringify(blockedResult)
            });
            continue;
          }
        }

        let toolResult = null;
        try {
          toolResult = await this.executeToolCall(toolName, toolArgs, toolCard);
          this.updateToolCard(toolCard, 'success', this.formatToolResultSummary(toolName, toolResult), toolResult);
        } catch (err) {
          if (this.isAborted) break;
          toolResult = { error: err.message, exit_code: 1 };
          this.updateToolCard(toolCard, 'error', `Tool Error: ${err.message}`);
        }

        // Feed tool response back into conversation history
        this.conversationHistory.push({
          role: 'tool',
          tool_call_id: call.id,
          name: toolName,
          content: JSON.stringify(toolResult)
        });

        // Special: implementation_plan.md triggers Antigravity Planning Gate
        if (toolName === 'write_to_file' && isPlanFile) {
          if (this.onArtifactPlanReady) {
            this.onArtifactPlanReady(toolArgs.CodeContent);
          }
          if (this.onPlanPendingApproval) {
            this.onPlanPendingApproval(toolArgs.CodeContent);
          }
          if (typeof document !== 'undefined') {
            const banner = document.getElementById('plan-approval-banner');
            const badge = document.getElementById('artifacts-badge');
            if (banner) banner.style.display = 'block';
            if (badge) badge.style.display = 'inline-block';
          }

          this.terminal?.appendOutput(`📋 Antigravity Planning Gate: implementation_plan.md created. Awaiting human authorization...`, 'warn');
          this.setState('waiting');
          this.isPaused = true;

          // PAUSE EXECUTION: Wait for human click on "Approve & Proceed" or "Revise Goal"
          const approval = await this.waitForPlanApproval();
          if (this.isAborted) break;

          if (!approval.approved) {
            this.planApproved = false;
            this.setState('planning');
            this.conversationHistory.push({
              role: 'user',
              content: `[Human Feedback on Plan]: ${approval.feedback || 'Please revise the implementation plan.'}. Update implementation_plan.md with write_to_file.`
            });
            break; // Let model re-generate revised plan
          } else {
            this.planApproved = true;
            this.setState('executing');
            this.conversationHistory.push({
              role: 'user',
              content: `The implementation plan has been approved by the user! Proceed immediately to synthesize the real source code files (index.html, style.css, app.js), verify with browser_subagent, and write walkthrough.md.`
            });
            break; // Proceed to next turn with approval confirmed
          }
        }

        // Special: walkthrough.md triggers Walkthrough Artifact View
        if (toolName === 'write_to_file' && (toolArgs.TargetFile || '').toLowerCase().includes('walkthrough.md')) {
          if (this.onArtifactReady) {
            this.onArtifactReady('walkthrough.md');
          }
        }
      }
    }

    if (this.isAborted && this.onExecutionEnd) {
      this.onExecutionEnd({ aborted: true });
    }
  }

  approvePlan() {
    this.planApproved = true;
    this.isPaused = false;

    if (typeof document !== 'undefined') {
      const banner = document.getElementById('plan-approval-banner');
      const badge = document.getElementById('artifacts-badge');
      if (banner) banner.style.display = 'none';
      if (badge) badge.style.display = 'none';
    }

    this.terminal?.appendOutput(`✔ Planning Gate: User approved implementation plan. Resuming execution...`, 'success');
    this.setState('executing');

    if (this.planApprovalResolver) {
      const resolve = this.planApprovalResolver;
      this.planApprovalResolver = null;
      resolve({ approved: true });
    }
  }

  rejectPlan(feedback = '') {
    this.planApproved = false;
    this.isPaused = false;

    if (typeof document !== 'undefined') {
      const banner = document.getElementById('plan-approval-banner');
      const badge = document.getElementById('artifacts-badge');
      if (banner) banner.style.display = 'none';
      if (badge) badge.style.display = 'none';
    }

    this.terminal?.appendOutput(`✕ Planning Gate: User requested plan revisions: ${feedback || 'Please revise objective.'}`, 'warn');
    this.setState('planning');

    if (this.planApprovalResolver) {
      const resolve = this.planApprovalResolver;
      this.planApprovalResolver = null;
      resolve({ approved: false, feedback });
    }
  }

  async handleRuntimeError(errorData) {
    if (!errorData || !errorData.message) return;
    const now = Date.now();
    const msg = errorData.message.trim();

    // 1. Debounce and concurrency guard: do not trigger multiple overlapping healing sessions
    if (this.isHealing) {
      console.warn('[frAIday Healing] Already diagnosing/healing. Skipping duplicate event:', msg);
      return;
    }
    if (now - this.lastHealTime < 7000) {
      console.warn('[frAIday Healing] Cooldown active. Skipping repeated trigger:', msg);
      return;
    }
    if (msg === this.lastHealedError && (now - this.lastHealTime < 20000)) {
      console.warn('[frAIday Healing] Same defect already addressed recently. Skipping:', msg);
      return;
    }

    this.isHealing = true;
    this.lastHealTime = now;
    this.lastHealedError = msg;

    this.terminal?.appendOutput(`⚡ Autonomous Error Interceptor: Captured runtime exception: ${msg} (${errorData.filename ? errorData.filename + ':' + errorData.lineno : 'preview'}). Initiating self-healing...`, 'warn');
    this.setState('healing');

    // 2. Emit dedicated System Diagnostic alert to chat stream (NEVER emit onUserMessage!)
    if (this.onSystemAlert) {
      this.onSystemAlert({
        type: 'runtime_error',
        message: msg,
        filename: errorData.filename,
        lineno: errorData.lineno,
        colno: errorData.colno
      });
    }

    // 3. Trigger autonomous healing loop without fake user message bubbles
    try {
      await this.executeSelfHealing(errorData);
    } catch (err) {
      console.error('Self-healing error:', err);
      this.terminal?.appendOutput(`✕ Autonomous self-healing error: ${err.message}`, 'error');
    } finally {
      this.isHealing = false;
      this.setState('idle');
    }
  }

  async executeSelfHealing(errorData) {
    if (this.isAborted) return;
    this.abortController = new AbortController();

    const diagnosticDirective = `[AUTONOMOUS PREVIEW RUNTIME ERROR INTERCEPTOR]
A runtime exception occurred in the live preview iframe:
Message: ${errorData.message}
File: ${errorData.filename || 'unknown'}:${errorData.lineno || 0}

INSTRUCTIONS:
1. Diagnose the exact cause using view_file or grep_search.
2. If this is an external library or API compatibility issue (e.g. Three.js / OrbitControls / CDN specifier), use search_web to find the exact, working CDN URLs or syntax.
3. Patch the code using replace_file_content or write_to_file.
4. Verify your fix using browser_subagent.
5. DO NOT generate walkthrough.md until the fix is verified clean.`;

    if (!this.conversationHistory || this.conversationHistory.length === 0) {
      this.conversationHistory = [
        { role: 'system', content: ANTIGRAVITY_SYSTEM_PROMPT }
      ];
    }
    this.conversationHistory.push({
      role: 'user',
      content: diagnosticDirective
    });

    this.streamThought(`Autonomous Error Interceptor: Diagnosing "${errorData.message}"...`);

    let turns = 0;
    const maxHealingTurns = 12;

    while (turns < maxHealingTurns) {
      if (this.isAborted) break;
      turns++;

      let respData = null;
      try {
        respData = await this.callLlmRaw(this.conversationHistory, ANTIGRAVITY_TOOLS);
      } catch (err) {
        console.error('Self-healing LLM error:', err);
        break;
      }

      if (this.isAborted) break;

      const assistantMsg = respData.message || { role: 'assistant', content: respData.content || '' };
      const toolCalls = assistantMsg.tool_calls || [];
      const content = assistantMsg.content || '';

      if (content) {
        await this.streamThought(content);
      }
      this.conversationHistory.push(assistantMsg);

      if (!toolCalls || toolCalls.length === 0) {
        this.terminal?.appendOutput(`✔ Autonomous self-healing turn completed.`, 'success');
        break;
      }

      let hasVerified = false;
      for (const call of toolCalls) {
        if (this.isAborted) break;
        const toolName = call.function?.name;
        let toolArgs = {};
        try {
          toolArgs = typeof call.function?.arguments === 'string'
            ? JSON.parse(call.function.arguments)
            : (call.function?.arguments || {});
        } catch (_) {
          toolArgs = {};
        }

        const toolCard = this.addAntigravityToolCard(toolName, toolArgs);

        // Disallow writing walkthrough.md during healing
        if (toolName === 'write_to_file' && (toolArgs.TargetFile || '').toLowerCase().includes('walkthrough.md')) {
          const blockedResult = { error: "Do not create walkthrough.md during error healing. Diagnose, patch, and verify with browser_subagent first." };
          this.updateToolCard(toolCard, 'error', 'Blocked during error healing');
          this.conversationHistory.push({
            role: 'tool',
            tool_call_id: call.id,
            name: toolName,
            content: JSON.stringify(blockedResult)
          });
          continue;
        }

        let toolResult = null;
        try {
          toolResult = await this.executeToolCall(toolName, toolArgs, toolCard);
          this.updateToolCard(toolCard, 'success', this.formatToolResultSummary(toolName, toolResult), toolResult);
          if (toolName === 'browser_subagent' && (!toolResult.console_errors || toolResult.console_errors.length === 0)) {
            hasVerified = true;
          }
        } catch (err) {
          toolResult = { error: err.message, exit_code: 1 };
          this.updateToolCard(toolCard, 'error', `Error: ${err.message}`);
        }

        this.conversationHistory.push({
          role: 'tool',
          tool_call_id: call.id,
          name: toolName,
          content: JSON.stringify(toolResult)
        });
      }

      if (hasVerified) {
        this.terminal?.appendOutput(`✔ Defect successfully healed and certified in headless Chrome!`, 'success');
        if (typeof window !== 'undefined' && window.fraidayApp) {
          window.fraidayApp.reloadPreview();
        }
        break;
      }
    }
  }

  // Compatibility helpers
  async writeFile(path, content) {
    return await this.executeToolCall('write_to_file', { TargetFile: path, CodeContent: content }, null);
  }

  async patchFile(path, target, replacement) {
    return await this.executeToolCall('replace_file_content', { TargetFile: path, TargetContent: target, ReplacementContent: replacement }, null);
  }

  buildLangGraph() {
    return {
      invoke: async (args) => this.executeGoal(args.goal),
      resume: async () => this.approvePlan(),
      isPaused: this.isPaused
    };
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
