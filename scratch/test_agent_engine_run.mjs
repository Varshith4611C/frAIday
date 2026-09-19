import { AgentEngine } from '../js/agent/agent-engine.js';

const logs = [];
const dummyTerminal = {
  appendCommand: (cmd) => console.log(`[TERMINAL CMD] $ ${cmd}`),
  appendOutput: (out, type) => console.log(`[TERMINAL ${type?.toUpperCase()}] ${out}`)
};

const engine = new AgentEngine({
  terminal: dummyTerminal,
  apiBase: 'http://localhost:8080'
});

console.log("Starting autonomous agent goal execution...");
const approvalInterval = setInterval(() => {
  if (engine.isPaused) {
    console.log("[TEST HARNESS] User clicked Approve & Proceed at Planning Gate!");
    engine.approvePlan();
  }
}, 300);

await engine.executeGoal("Create a sleek cyberpunk stopwatch app in workspace with index.html, style.css, and app.js. Run list_dir to confirm files exist, inspect with browser_subagent, and write walkthrough.md.");
clearInterval(approvalInterval);
console.log("\nGoal execution loop completed! Turns taken:", engine.turnCount);


