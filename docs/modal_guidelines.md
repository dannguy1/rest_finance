# Modal Dialog Guidelines

## Overview

This document outlines the standardized approach for creating modal dialogs in our financial data processing application. These guidelines ensure consistent styling, behavior, and user experience across all modal components.

## Design Principles

### 1. **Visibility & Accessibility**
- Modals must be clearly visible with solid backgrounds
- High z-index (1060) to ensure proper layering
- Proper contrast and readability
- Keyboard navigation support

### 2. **Professional Appearance**
- Clean, modern design with shadows and borders
- Consistent color scheme and typography
- Proper spacing and visual hierarchy
- Icon integration for better UX

### 3. **User Experience**
- Static backdrop to prevent accidental closing
- Clear action buttons with descriptive text
- Loading states and feedback
- Responsive design for all screen sizes

## HTML Structure

### Standard Modal Template

```html
<!-- Modal Container -->
<div class="modal fade" id="modalId" tabindex="-1" aria-modal="true" role="dialog" style="z-index: 1060;">
    <div class="modal-dialog modal-xl">
        <div class="modal-content border-0 shadow-lg" style="background-color: white;">
            
            <!-- Header -->
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title">
                    <i class="bi bi-[icon-name] me-2"></i>
                    <span id="modalTitle">Modal Title</span>
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            
            <!-- Body -->
            <div class="modal-body p-4" style="background-color: white;">
                <!-- Modal content goes here -->
            </div>
            
            <!-- Footer -->
            <div class="modal-footer bg-light">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    <i class="bi bi-x-circle me-2"></i>
                    Cancel
                </button>
                <button type="button" class="btn btn-primary">
                    <i class="bi bi-[action-icon] me-2"></i>
                    Primary Action
                </button>
            </div>
        </div>
    </div>
</div>
```

## CSS Classes & Styling

### Required Classes
- `modal fade` - Bootstrap modal classes
- `border-0 shadow-lg` - Remove borders, add shadow
- `bg-primary text-white` - Header styling
- `bg-light` - Footer background
- `btn-close-white` - White close button for colored headers

### Inline Styles
```css
/* Modal container */
z-index: 1060;

/* Modal content */
background-color: white;

/* Modal body */
background-color: white;
```

## JavaScript Initialization

### Standard Modal Show Function

```javascript
function showModal(modalId, options = {}) {
    // Remove existing modal and overlays
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        if (bootstrap.Modal.getInstance(existingModal)) {
            bootstrap.Modal.getInstance(existingModal).dispose();
        }
    }
    
    // Remove all modal backdrops and clean up body
    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    // Initialize and show modal with static backdrop
    const modal = new bootstrap.Modal(existingModal, { 
        backdrop: 'static', 
        keyboard: true, 
        focus: true 
    });
    
    // Show modal
    modal.show();
    
    // Make backdrop fully opaque
    setTimeout(() => {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.style.opacity = '0.5';
        }
    }, 10);
}
```

## Modal Types & Color Schemes

### 1. **Primary Modal** (Default)
- Header: `bg-primary text-white`
- Icon: `bi-gear`, `bi-file-earmark-text`, `bi-plus-circle`
- Use for: Configuration, creation, general actions

### 2. **Success Modal**
- Header: `bg-success text-white`
- Icon: `bi-check-circle`, `bi-check2-circle`
- Use for: Confirmations, successful actions

### 3. **Warning Modal**
- Header: `bg-warning text-dark`
- Icon: `bi-exclamation-triangle`, `bi-exclamation-circle`
- Use for: Warnings, confirmations with caution

### 4. **Danger Modal**
- Header: `bg-danger text-white`
- Icon: `bi-exclamation-triangle`, `bi-trash`
- Use for: Deletions, destructive actions

### 5. **Info Modal**
- Header: `bg-info text-white`
- Icon: `bi-info-circle`, `bi-question-circle`
- Use for: Information, help, guidance

## Button Guidelines

### Button Types & Icons

| Action | Class | Icon | Description |
|--------|-------|------|-------------|
| Cancel | `btn-secondary` | `bi-x-circle` | Close modal without action |
| Save | `btn-primary` | `bi-save` | Save changes |
| Delete | `btn-danger` | `bi-trash` | Delete/remove item |
| Confirm | `btn-success` | `bi-check-circle` | Confirm action |
| Validate | `btn-info` | `bi-check-circle` | Validate input |
| Download | `btn-outline-primary` | `bi-download` | Download file |
| Edit | `btn-outline-secondary` | `bi-pencil` | Edit item |

### Button Order
1. **Cancel/Close** (left)
2. **Secondary Actions** (middle)
3. **Primary Action** (right)

## Content Guidelines

### Form Layout
```html
<div class="row mb-4">
    <div class="col-md-6">
        <label for="fieldId" class="form-label">Field Label *</label>
        <input type="text" class="form-control" id="fieldId" required>
        <div class="form-text">Help text or description</div>
    </div>
    <div class="col-md-6">
        <!-- Another field -->
    </div>
</div>
```

### Section Headers
```html
<h6 class="mb-3">
    <i class="bi bi-[icon] me-2"></i>
    Section Title
</h6>
```

### Alerts in Modals
```html
<div class="alert alert-[type] border-0 shadow-sm">
    <div class="d-flex align-items-center mb-2">
        <i class="bi bi-[icon] me-2"></i>
        <h6 class="mb-0">Alert Title</h6>
    </div>
    <p class="mb-0">Alert message content</p>
</div>
```

## Responsive Design

### Modal Sizes
- `modal-sm` - Small modals (300px)
- `modal` - Default size (500px)
- `modal-lg` - Large modals (800px)
- `modal-xl` - Extra large modals (1140px)

### Mobile Considerations
- Ensure touch-friendly button sizes
- Adequate spacing between interactive elements
- Scrollable content for long forms
- Proper viewport handling

## Accessibility

### ARIA Attributes
```html
<div class="modal fade" 
     id="modalId" 
     tabindex="-1" 
     aria-modal="true" 
     role="dialog" 
     aria-labelledby="modalTitle">
```

### Keyboard Navigation
- Tab order follows logical flow
- Escape key closes modal
- Enter key triggers primary action
- Focus management on open/close

## Testing Checklist

### Visual Testing
- [ ] Modal appears above all other content
- [ ] Backdrop is properly opaque
- [ ] Text is readable and properly contrasted
- [ ] Buttons are clearly visible and accessible
- [ ] Modal is properly centered

### Functional Testing
- [ ] Modal opens and closes correctly
- [ ] Static backdrop prevents accidental closing
- [ ] Keyboard navigation works
- [ ] Focus management is correct
- [ ] Form validation works (if applicable)

### Responsive Testing
- [ ] Modal works on mobile devices
- [ ] Content is scrollable if needed
- [ ] Touch interactions work properly
- [ ] No horizontal scrolling issues

## Common Patterns

### 1. **Create/Edit Pattern**
```javascript
function showCreateModal() {
    resetForm();
    document.getElementById('modalTitle').textContent = 'Create New Item';
    showModal('modalId');
}

function showEditModal(data) {
    populateForm(data);
    document.getElementById('modalTitle').textContent = `Edit Item: ${data.name}`;
    showModal('modalId');
}
```

### 2. **Confirmation Pattern**
```javascript
function showDeleteModal(itemName) {
    document.getElementById('deleteItemName').textContent = itemName;
    showModal('deleteModal');
}
```

### 3. **Loading Pattern**
```javascript
function showLoadingModal() {
    document.getElementById('modalContent').innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">Processing...</p>
        </div>
    `;
    showModal('loadingModal');
}
```

## Best Practices

### Do's
- ✅ Use consistent styling across all modals
- ✅ Include appropriate icons in titles and buttons
- ✅ Provide clear, descriptive button text
- ✅ Handle loading states gracefully
- ✅ Implement proper error handling
- ✅ Test on multiple devices and screen sizes

### Don'ts
- ❌ Don't use transparent or semi-transparent backgrounds
- ❌ Don't skip proper cleanup of existing modals
- ❌ Don't forget keyboard accessibility
- ❌ Don't use unclear or generic button text
- ❌ Don't ignore mobile user experience

## Examples

### File Analysis Modal
```html
<div class="modal fade" id="fileAnalysisModal" tabindex="-1" aria-modal="true" role="dialog" style="z-index: 1060;">
    <div class="modal-dialog modal-xl">
        <div class="modal-content border-0 shadow-lg" style="background-color: white;">
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title">
                    <i class="bi bi-file-earmark-text me-2"></i>
                    File Analysis: ${filename}
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4" style="background-color: white;">
                <!-- Analysis content -->
            </div>
            <div class="modal-footer bg-light">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    <i class="bi bi-x-circle me-2"></i>
                    Close
                </button>
            </div>
        </div>
    </div>
</div>
```

### Delete Confirmation Modal
```html
<div class="modal fade" id="deleteModal" tabindex="-1" aria-modal="true" role="dialog" style="z-index: 1060;">
    <div class="modal-dialog">
        <div class="modal-content border-0 shadow-lg" style="background-color: white;">
            <div class="modal-header bg-danger text-white">
                <h5 class="modal-title">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Confirm Delete
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4" style="background-color: white;">
                <p>Are you sure you want to delete <strong id="deleteItemName"></strong>?</p>
                <p class="text-muted">This action cannot be undone.</p>
            </div>
            <div class="modal-footer bg-light">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    <i class="bi bi-x-circle me-2"></i>
                    Cancel
                </button>
                <button type="button" class="btn btn-danger" onclick="confirmDelete()">
                    <i class="bi bi-trash me-2"></i>
                    Delete
                </button>
            </div>
        </div>
    </div>
</div>
```

## Maintenance

### Version Control
- Keep modal guidelines updated with new patterns
- Document any deviations and their rationale
- Review and update guidelines quarterly

### Code Review Checklist
- [ ] Follows modal structure guidelines
- [ ] Uses appropriate color scheme
- [ ] Includes proper icons
- [ ] Implements correct JavaScript initialization
- [ ] Passes accessibility requirements
- [ ] Works on all target devices

---

*Last Updated: July 4, 2025*
*Version: 1.0* 