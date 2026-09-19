/**
 * frAIday — Production Real Code Editor & Diff Studio
 * Reads and writes real files to /api/workspace/file
 */

import { highlightCode } from '../utils/syntax-highlighter.js';

export class CodeEditorComponent {
  constructor(container, onTriggerLens, onFileSaved) {
    this.container = container;
    this.onTriggerLens = onTriggerLens;
    this.onFileSaved = onFileSaved;
    this.currentFile = null;
    this.currentContent = '';
    this.currentDiff = null;
    this.viewMode = 'code'; // 'code' or 'diff'
    this.isDirty = false;
  }

  clear() {
    this.currentFile = null;
    this.currentContent = '';
    this.currentDiff = null;
    this.isDirty = false;
    this.render();
  }

  async loadFile(filepath, diffContent = null) {
    if (!filepath) {
      this.clear();
      return;
    }

    this.currentFile = filepath;
    this.currentDiff = diffContent;
    this.isDirty = false;

    try {
      const resp = await fetch(`/api/workspace/file?path=${encodeURIComponent(filepath)}`);
      if (resp.ok) {
        const data = await resp.json();
        this.currentContent = data.content || '';
      } else {
        this.currentContent = '';
      }
    } catch (e) {
      console.error('Failed to load file:', e);
      this.currentContent = '';
    }

    this.render();
  }

  setContent(content, diff = null) {
    this.currentContent = content;
    this.currentDiff = diff;
    this.isDirty = false;
    this.render();
  }

  async saveCurrentFile() {
    if (!this.currentFile) return;
    const textarea = this.container.querySelector('#editor-textarea');
    if (textarea) {
      this.currentContent = textarea.value;
    }

    try {
      const resp = await fetch('/api/workspace/file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: this.currentFile,
          content: this.currentContent
        })
      });
      if (resp.ok) {
        this.isDirty = false;
        const saveBtn = this.container.querySelector('#btn-save-code');
        if (saveBtn) {
          saveBtn.innerText = '✅ Saved';
          setTimeout(() => { saveBtn.innerText = '💾 Save'; }, 1800);
        }
        if (this.onFileSaved) this.onFileSaved(this.currentFile);
      }
    } catch (e) {
      alert('Failed to save file: ' + e.message);
    }
  }

  render() {
    if (!this.container) return;

    if (!this.currentFile) {
      this.container.innerHTML = `
        <div style="height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:var(--text-muted);">
          <span style="font-size:36px;">📄</span>
          <span style="font-size:13px;font-weight:600;">No file open</span>
          <span style="font-size:11.5px;color:#64748b;">Select a file from the workspace explorer or tell the agent to create one.</span>
        </div>
      `;
      return;
    }

    const lang = this.detectLanguage(this.currentFile);
    const lineCount = this.currentContent.split('\n').length;
    const gutterLines = Array.from({ length: Math.max(lineCount, 1) }, (_, i) => `<div class="gutter-line">${i + 1}</div>`).join('');

    this.container.innerHTML = `
      <div class="editor-wrapper">
        <div class="editor-toolbar">
          <div class="editor-filename">
            <span>📄</span>
            <span>${this.currentFile}</span>
            ${this.isDirty ? '<span style="color:#f59e0b;font-size:10px;">● Unsaved</span>' : ''}
          </div>
          <div class="editor-actions">
            ${this.currentDiff ? `
              <div class="editor-view-toggle">
                <button class="editor-toggle-btn ${this.viewMode === 'code' ? 'active' : ''}" data-mode="code">Source Code</button>
                <button class="editor-toggle-btn ${this.viewMode === 'diff' ? 'active' : ''}" data-mode="diff">Inline Diff</button>
              </div>
            ` : ''}
            <button id="btn-save-code" class="btn btn-primary btn-sm">💾 Save</button>
            <button id="btn-copy-code" class="btn btn-secondary btn-sm">📋 Copy</button>
          </div>
        </div>

        <!-- Antigravity Inline Code Lenses Sub-toolbar -->
        <div class="editor-lenses-bar">
          <span class="lenses-label">✨ Lenses:</span>
          <button class="lens-action-btn" data-action="refactor">✨ Refactor</button>
          <button class="lens-action-btn test" data-action="test">🧪 Generate Tests</button>
          <button class="lens-action-btn explain" data-action="explain">🔍 Explain Code</button>
          <button class="lens-action-btn" data-action="audit" style="color:#fbbf24;border-color:rgba(245,158,11,0.3);background:rgba(245,158,11,0.1);">🛡️ Security Audit</button>
        </div>

        <div class="editor-viewport">
          <div class="editor-gutter" id="editor-gutter-lines">
            ${gutterLines}
          </div>
          <div class="editor-content" id="editor-code-body">
            ${this.viewMode === 'diff' && this.currentDiff ? `
              <div class="code-text-area" id="editor-diff-content">${highlightCode(this.currentDiff, 'diff')}</div>
            ` : `
              <textarea id="editor-textarea" spellcheck="false" wrap="off">${escapeHtml(this.currentContent)}</textarea>
            `}
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelectorAll('.editor-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.viewMode = btn.getAttribute('data-mode');
        this.render();
      });
    });

    const saveBtn = this.container.querySelector('#btn-save-code');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => this.saveCurrentFile());
    }

    const textarea = this.container.querySelector('#editor-textarea');
    const gutter = this.container.querySelector('#editor-gutter-lines');

    if (textarea && gutter) {
      // Synchronize vertical scrolling with line numbers
      textarea.addEventListener('scroll', () => {
        gutter.scrollTop = textarea.scrollTop;
      });

      // Forward wheel scrolling on the line numbers gutter to the textarea
      gutter.addEventListener('wheel', (e) => {
        textarea.scrollTop += e.deltaY;
        e.preventDefault();
      }, { passive: false });

      // Dynamically update gutter line numbers on input
      const updateGutter = () => {
        this.currentContent = textarea.value;
        this.isDirty = true;
        const lineCount = (textarea.value.match(/\n/g) || []).length + 1;
        gutter.innerHTML = Array.from({ length: Math.max(lineCount, 1) }, (_, i) => `<div class="gutter-line">${i + 1}</div>`).join('');
        gutter.scrollTop = textarea.scrollTop;
      };

      textarea.addEventListener('input', updateGutter);

      // Support Tab key indentation without losing focus or breaking scroll
      textarea.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
          e.preventDefault();
          this.saveCurrentFile();
        } else if (e.key === 'Tab') {
          e.preventDefault();
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          textarea.value = textarea.value.substring(0, start) + '  ' + textarea.value.substring(end);
          textarea.selectionStart = textarea.selectionEnd = start + 2;
          updateGutter();
        }
      });
    }

    const copyBtn = this.container.querySelector('#btn-copy-code');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const textToCopy = textarea ? textarea.value : this.currentContent;
        navigator.clipboard.writeText(textToCopy);
        copyBtn.innerText = '✅ Copied!';
        setTimeout(() => { copyBtn.innerText = '📋 Copy'; }, 2000);
      });
    }

    this.container.querySelectorAll('.lens-action-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.getAttribute('data-action');
        if (this.onTriggerLens) {
          const currentVal = textarea ? textarea.value : this.currentContent;
          this.onTriggerLens(action, this.currentFile, currentVal);
        }
      });
    });
  }

  detectLanguage(filepath) {
    if (filepath.endsWith('.html')) return 'html';
    if (filepath.endsWith('.css')) return 'css';
    if (filepath.endsWith('.sql')) return 'sql';
    if (filepath.endsWith('.json')) return 'json';
    if (filepath.endsWith('.py')) return 'python';
    return 'javascript';
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
