/**
 * frAIday — Interactive Task DAG Visualizer Component
 */

export class DagCanvasComponent {
  constructor(container, onSelectNode) {
    this.container = container;
    this.onSelectNode = onSelectNode;
    this.nodes = [];
    this.activeNodeId = null;
  }

  setNodes(nodes, activeNodeId = null) {
    this.nodes = nodes || [];
    this.activeNodeId = activeNodeId;
    this.render();
  }

  clear() {
    this.nodes = [];
    this.activeNodeId = null;
    this.render();
  }

  updateNodeStatus(nodeId, newStatus) {
    const node = this.nodes.find(n => n.id === nodeId);
    if (node) {
      node.status = newStatus;
      this.render();
    }
  }

  render() {
    if (!this.container) return;

    if (this.nodes.length === 0) {
      this.container.innerHTML = `
        <div class="dag-wrapper" style="align-items:center;justify-content:center;color:var(--text-muted);">
          <div style="text-align:center;padding:40px;">
            <div style="font-size:36px;margin-bottom:12px;">🕸️</div>
            <div style="font-size:14px;font-weight:700;color:#f8fafc;margin-bottom:6px;">No Active Plan</div>
            <div style="font-size:12px;">Enter an objective in the prompt bar to generate a task execution DAG.</div>
          </div>
        </div>
      `;
      return;
    }

    this.container.innerHTML = `
      <div class="dag-wrapper">
        <div class="dag-toolbar">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-size:13px;font-weight:700;">Task DAG & Dependency Graph</span>
            <span class="brand-tag">${this.nodes.length} Stages</span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;font-size:11px;color:var(--text-muted);">
            <span>🟢 Completed</span>
            <span>🔵 Running</span>
            <span>🟡 HITL Approval</span>
            <span>🟣 Self-Healed</span>
          </div>
        </div>

        <div class="dag-canvas-area">
          <div class="dag-flow-container">
            ${this.nodes.map((node, index) => this.renderNode(node, index)).join('')}
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  renderNode(node, index) {
    const isLast = index === this.nodes.length - 1;
    const isCurrent = node.id === this.activeNodeId || node.status === 'active';
    const statusClass = node.status || 'pending';

    const statusBadges = {
      completed: '<span class="tool-badge success">✔ COMPLETED</span>',
      active: '<span class="tool-badge running">⚡ EXECUTING</span>',
      waiting: '<span class="tool-badge pending">⏳ WAITING APPROVAL</span>',
      healed: '<span class="tool-badge" style="background:rgba(236,72,153,0.2);color:#ec4899;">💖 SELF-HEALED</span>',
      pending: '<span class="tool-badge" style="background:rgba(255,255,255,0.08);color:#94a3b8;">QUEUED</span>'
    };

    return `
      <div class="dag-node-card ${statusClass} ${isCurrent ? 'active' : ''}" data-id="${node.id}">
        <div class="dag-node-header">
          <div class="dag-node-title">
            <span style="color:var(--text-muted);font-family:var(--font-mono);font-size:11px;">#${String(index + 1).padStart(2, '0')}</span>
            <span>${node.title}</span>
          </div>
          ${statusBadges[node.status] || statusBadges.pending}
        </div>
        <div class="dag-node-desc">${node.desc}</div>
      </div>
      ${!isLast ? '<div class="dag-connector"></div>' : ''}
    `;
  }

  bindEvents() {
    this.container.querySelectorAll('.dag-node-card').forEach(card => {
      card.addEventListener('click', () => {
        const nodeId = card.getAttribute('data-id');
        const node = this.nodes.find(n => n.id === nodeId);
        if (node && this.onSelectNode) {
          this.onSelectNode(node);
        }
      });
    });
  }
}
