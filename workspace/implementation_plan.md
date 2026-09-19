# Amazon Shopping Website

## Goal Description
Create a lightweight, responsive e‑commerce front‑end that mimics a simplified Amazon shopping experience. The site will display a grid of product cards, allow users to add items to a cart, view cart contents, and proceed to checkout. No backend is required; all data will be stored in `localStorage` for persistence across page reloads.

The architecture will consist of:
- **index.html** – Main entry point, includes Bootstrap for layout and styling.
- **style.css** – Custom styles for product cards and layout tweaks.
- **app.js** – Handles product rendering, cart logic, and UI interactions.
- **products.json** – Sample product data (optional, can be embedded in JS).

The site will be served locally via a simple HTTP server (e.g., `python -m http.server 8080`).

## User Review Required
- Verify CDN URLs for Bootstrap and Font Awesome.
- Confirm that the cart uses `localStorage` and that the checkout button simply displays a confirmation modal.

## Open Questions
- Should we include user authentication? (No – keep it stateless.)
- Do we need to support multiple currencies? (No – use USD.)
- Any specific design guidelines or color palette? (Use Bootstrap default theme.)

## Proposed Changes
### index.html
#### [NEW] index.html

### style.css
#### [MODIFY] style.css

### app.js
#### [NEW] app.js

### products.json
#### [NEW] products.json

## Verification Plan
### Automated Tests
No automated tests are required for this front‑end only project.

### Manual Verification
1. Launch a local server: `python -m http.server 8080`.
2. Open `http://localhost:8080/workspace/index.html` in a headless browser.
3. Verify:
   - Product grid displays correctly.
   - Add to cart button updates cart count.
   - Cart modal shows correct items and total.
   - No console errors.

Use the `browser_subagent` tool to capture a screenshot and confirm zero console errors.
