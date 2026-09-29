// app.js – Simple calculator logic (vanilla JS)
// Handles button clicks, keyboard input, and basic expression evaluation.

(() => {
    const display = document.getElementById('display');
    const buttons = document.querySelectorAll('.btn[data-key]');
    const clearBtn = document.getElementById('clear');
    const equalsBtn = document.getElementById('equals');

    // Internal state
    let expression = '';
    let lastKey = null;

    const updateDisplay = () => {
        display.textContent = expression || '0';
    };

    const append = (char) => {
        // Prevent multiple operators in a row
        const operators = '+-*/';
        if (operators.includes(char)) {
            if (!expression) return; // cannot start with operator
            if (operators.includes(lastKey)) {
                // replace the previous operator
                expression = expression.slice(0, -1) + char;
            } else {
                expression += char;
            }
        } else if (char === '.') {
            // Prevent multiple decimals in the current number segment
            const parts = expression.split(/[+\-*/]/);
            const current = parts[parts.length - 1];
            if (current.includes('.')) return;
            expression += char;
        } else {
            expression += char;
        }
        lastKey = char;
        updateDisplay();
    };

    const clearAll = () => {
        expression = '';
        lastKey = null;
        updateDisplay();
    };

    const evaluate = () => {
        if (!expression) return;
        try {
            // Use Function constructor for safe eval of arithmetic only
            // Replace any accidental leading operator
            const safeExpr = expression.replace(/^([+\-*/])/, '');
            // eslint-disable-next-line no-new-func
            const result = Function(`'use strict'; return (${safeExpr})`)();
            expression = Number.isFinite(result) ? String(result) : '';
        } catch (e) {
            expression = 'Error';
        }
        lastKey = null;
        updateDisplay();
    };

    // Button click handlers
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.getAttribute('data-key');
            append(key);
        });
    });

    clearBtn.addEventListener('click', clearAll);
    equalsBtn.addEventListener('click', evaluate);

    // Keyboard support
    document.addEventListener('keydown', (e) => {
        const key = e.key;
        if (key >= '0' && key <= '9') {
            append(key);
        } else if (['+', '-', '*', '/', '.'].includes(key)) {
            append(key);
        } else if (key === 'Enter' || key === '=') {
            evaluate();
        } else if (key === 'Escape' || key === 'c' || key === 'C') {
            clearAll();
        }
    });

    // Initialize display
    updateDisplay();
})();
