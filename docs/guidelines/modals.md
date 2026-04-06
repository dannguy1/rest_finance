# Modal Guidelines

## Purpose
Standardize modal structure, styling, and behavior across the UI.

## Structure

```html
<div class="modal fade" id="modalId" tabindex="-1" aria-modal="true" role="dialog" style="z-index: 1060;">
  <div class="modal-dialog modal-xl">
    <div class="modal-content border-0 shadow-lg" style="background-color: white;">
      <div class="modal-header bg-primary text-white">
        <h5 class="modal-title">
          <i class="bi bi-[icon-name] me-2"></i>
          Title
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body p-4" style="background-color: white;">
        <!-- Content -->
      </div>
      <div class="modal-footer bg-light">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary">Primary Action</button>
      </div>
    </div>
  </div>
</div>
```

## JavaScript Initialization

```javascript
function showModal(modalId) {
  const modalEl = document.getElementById(modalId);
  if (bootstrap.Modal.getInstance(modalEl)) {
    bootstrap.Modal.getInstance(modalEl).dispose();
  }
  document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
  document.body.classList.remove('modal-open');
  document.body.style.overflow = '';
  document.body.style.paddingRight = '';

  const modal = new bootstrap.Modal(modalEl, {
    backdrop: 'static',
    keyboard: true,
    focus: true
  });
  modal.show();
}
```

## Button Guidance

- Cancel on the left
- Primary action on the right
- Use icons consistently (`bi-*`)

## Accessibility

- `aria-modal="true"` and `role="dialog"`
- Keyboard support (escape closes)
- Clear focus states
