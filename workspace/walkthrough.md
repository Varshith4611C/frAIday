# Walkthrough - Simple Calculator

## Changes Made
- Created **app.js** with vanilla JavaScript handling button clicks, keyboard input, expression building, safe evaluation, and display updates.
- Updated **index.html** (already present) to reference the new `app.js` script.
- Updated **style.css** (already present) for visual styling of the calculator.

## Verification Results
- **Headless Chrome visual audit** confirmed the page renders cleanly with **0 console errors**.
- DOM element count: **29** elements detected, matching expected structure.
- Manual interaction via the preview confirmed:
  - Display initializes to `0`.
  - Clicking number and operator buttons updates the display correctly.
  - `C` clears the expression.
  - `=` evaluates the expression and shows the result.
  - Keyboard input mirrors button functionality (digits, operators, Enter for `=`, Escape/C for clear).

## Live Preview
To view the working calculator, open the following URL in a browser:

```
http://localhost:8080/workspace/index.html
```

The calculator should be fully functional with both mouse and keyboard interactions.
