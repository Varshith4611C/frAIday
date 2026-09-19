try {
  console.log('Testing file-tree.js...');
  await import('../js/components/file-tree.js');
  console.log('Testing code-editor.js...');
  await import('../js/components/code-editor.js');
  console.log('Testing dag-canvas.js...');
  await import('../js/components/dag-canvas.js');
  console.log('Testing terminal.js...');
  await import('../js/components/terminal.js');
  console.log('Testing knowledge-base.js...');
  await import('../js/agent/knowledge-base.js');
  console.log('Testing safety-policy.js...');
  await import('../js/agent/safety-policy.js');
  console.log('Testing langgraph-state-machine.js...');
  await import('../js/agent/langgraph-state-machine.js');
  console.log('Testing research-engine.js...');
  await import('../js/agent/research-engine.js');
  console.log('Testing browser-puppet.js...');
  await import('../js/agent/browser-puppet.js');
  console.log('Testing agent-engine.js...');
  await import('../js/agent/agent-engine.js');
  console.log('Testing app.js...');
  await import('../js/app.js');
  console.log('ALL MODULES IMPORTED CLEANLY!');
} catch (e) {
  console.error('IMPORT ERROR:', e);
}
