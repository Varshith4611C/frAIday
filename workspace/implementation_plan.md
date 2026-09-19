# Fix: Close Button Not Working

## Objective
The user reports that the close button on the modal is not working. We need to diagnose and fix the issue in the "Book My Show" web application.

## Current State Analysis
- `index.html` contains a modal with `id="modal"` and a close button with `id="close-modal"`.
- `app.js` defines a `closeModal()` function that adds the `hidden` class to the modal.
- `app.js` attaches a click event listener to `#close-modal` on `DOMContentLoaded`.
- The modal-