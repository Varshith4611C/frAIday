# Simple Calculator

**Goal**: Build a minimal web‑based calculator that adheres to the recalled project preferences (dark theme with cyan accents, vanilla JavaScript, plain CSS, responsive, accessible).

## User Review Required
- **UI Theme**: Dark background (`#121212`) with cyan accent (`#00bcd4`) for buttons and highlights.
- **Tech Stack**: Plain HTML, CSS, and vanilla JavaScript only. No external libraries or frameworks.
- **Responsiveness**: Layout should adapt to mobile widths (flex column on narrow screens).
- **Accessibility**: All buttons receive focus, have `aria-label`s, and can be operated via keyboard (Enter/Space).
- **File Naming**: `index.html`, `style.css`, `app.js` placed at the workspace root.

## Open Questions
1. Should the calculator support decimal numbers and a clear‑entry (`CE`) button, or just integer operations?
2. Desired operator set – basic (`+`, `-`, `*`, `/`) only, or include `%` and `±`?
3. Any specific layout preference (grid 4×4 vs. custom arrangement)?

## Proposed Changes
### UI
- **[NEW] index.html** – Basic page skeleton, container for the calculator, and script/style links.
- **[NEW] style.css** – Dark theme, cyan accent styling, responsive flex layout.
- **[NEW] app.js** – Vanilla JavaScript handling button clicks, keyboard input, display updates, and basic arithmetic logic.

## Verification Plan
### Automated Tests
- None required (project prefers manual verification). If needed later, a simple `npm test` script could be added.

### Manual Verification
1. **Launch a local static server** (e.g., `python -m http.server 8080`).
2. Open `http://localhost:8080/index.html` in a browser.
3. Verify:
   - Dark theme with cyan buttons.
   - All buttons are focusable and operable via keyboard.
   - Calculator correctly computes basic operations (including chained calculations).
   - Layout adapts on mobile‑width viewport.
4. Run a headless‑browser audit via `browser_subagent` to ensure **0 console errors** and a clean screenshot.

---
*Once you approve this plan, I will proceed to create the files and implement the calculator.*