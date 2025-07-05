/**
 * Garlic and Chives - UI Components
 * Reusable components for the application
 */

class Components {
    constructor() {
        this.init();
    }

    init() {
        this.setupModals();
        this.setupNotifications();
        this.setupLoading();
        this.setupFileUpload();
        this.setupDataTables();
    }

    // Modal Management
    setupModals() {
        this.modals = {};
        document.querySelectorAll('.modal').forEach(modal => {
            const modalId = modal.id;
            this.modals[modalId] = {
                element: modal,
                isOpen: false
            };

            // Close button functionality
            const closeBtn = modal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.closeModal(modalId));
            }

            // Click outside to close
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modalId);
                }
            });
        });
    }

    openModal(modalId, options = {}) {
        const modal = this.modals[modalId];
        if (!modal) return;

        modal.element.classList.remove('hidden');
        modal.isOpen = true;
        document.body.classList.add('modal-open');

        // Focus management
        const focusableElements = modal.element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }

        // Custom options
        if (options.onOpen) options.onOpen();
    }

    closeModal(modalId) {
        const modal = this.modals[modalId];
        if (!modal) return;

        modal.element.classList.add('hidden');
        modal.isOpen = false;
        document.body.classList.remove('modal-open');

        // Custom options
        if (options.onClose) options.onClose();
    }

    // Notification System
    setupNotifications() {
        this.notificationContainer = document.getElementById('flash-messages');
        if (!this.notificationContainer) {
            this.notificationContainer = document.createElement('div');
            this.notificationContainer.id = 'flash-messages';
            this.notificationContainer.className = 'flash-messages';
            document.body.appendChild(this.notificationContainer);
        }
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Close button
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => this.removeNotification(notification));

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => this.removeNotification(notification), duration);
        }

        this.notificationContainer.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.classList.add('show'), 10);
    }

    removeNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Loading Management
    setupLoading() {
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingMessage = document.getElementById('loading-message');
    }

    showLoading(message = 'Loading...') {
        if (this.loadingMessage) {
            this.loadingMessage.textContent = message;
        }
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('hidden');
        }
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('hidden');
        }
    }

    // File Upload Components
    setupFileUpload() {
        this.setupDragDrop();
        this.setupFileValidation();
    }

    setupDragDrop() {
        document.querySelectorAll('.drop-zone').forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('drag-over');
            });

            zone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                zone.classList.remove('drag-over');
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('drag-over');
                const files = Array.from(e.dataTransfer.files);
                this.handleFileDrop(files, zone);
            });
        });
    }

    setupFileValidation() {
        // File validation rules
        this.fileValidation = {
            maxSize: 50 * 1024 * 1024, // 50MB
            allowedTypes: ['.csv'],
            allowedMimeTypes: ['text/csv', 'application/csv']
        };
    }

    handleFileDrop(files, dropZone) {
        const validFiles = files.filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            this.showNotification('Please select valid CSV files', 'error');
            return;
        }

        // Trigger file upload
        const event = new CustomEvent('filesSelected', {
            detail: { files: validFiles, dropZone }
        });
        document.dispatchEvent(event);
    }

    validateFile(file) {
        // Check file size
        if (file.size > this.fileValidation.maxSize) {
            this.showNotification(`File ${file.name} is too large (max 50MB)`, 'error');
            return false;
        }

        // Check file type
        const isValidType = this.fileValidation.allowedTypes.some(ext => 
            file.name.toLowerCase().endsWith(ext)
        ) || this.fileValidation.allowedMimeTypes.includes(file.type);

        if (!isValidType) {
            this.showNotification(`File ${file.name} is not a valid CSV file`, 'error');
            return false;
        }

        return true;
    }

    // Data Table Components
    setupDataTables() {
        this.setupSortableTables();
        this.setupSearchableTables();
        this.setupPagination();
    }

    setupSortableTables() {
        document.querySelectorAll('.sortable-table').forEach(table => {
            const headers = table.querySelectorAll('th[data-sort]');
            headers.forEach(header => {
                header.addEventListener('click', () => {
                    const column = header.dataset.sort;
                    const direction = header.dataset.direction === 'asc' ? 'desc' : 'asc';
                    this.sortTable(table, column, direction);
                    
                    // Update header state
                    headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
                    header.classList.add(`sort-${direction}`);
                    header.dataset.direction = direction;
                });
            });
        });
    }

    sortTable(table, column, direction) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            const aValue = a.querySelector(`td[data-${column}]`)?.dataset[column] || '';
            const bValue = b.querySelector(`td[data-${column}]`)?.dataset[column] || '';
            
            if (direction === 'asc') {
                return aValue.localeCompare(bValue);
            } else {
                return bValue.localeCompare(aValue);
            }
        });

        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
    }

    setupSearchableTables() {
        document.querySelectorAll('.searchable-table').forEach(table => {
            const searchInput = table.querySelector('.table-search');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.filterTable(table, e.target.value);
                });
            }
        });
    }

    filterTable(table, searchTerm) {
        const rows = table.querySelectorAll('tbody tr');
        const term = searchTerm.toLowerCase();

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }

    setupPagination() {
        document.querySelectorAll('.pagination').forEach(pagination => {
            const itemsPerPage = parseInt(pagination.dataset.itemsPerPage) || 10;
            const table = document.querySelector(pagination.dataset.table);
            
            if (table) {
                this.setupTablePagination(table, pagination, itemsPerPage);
            }
        });
    }

    setupTablePagination(table, pagination, itemsPerPage) {
        const rows = table.querySelectorAll('tbody tr');
        const totalPages = Math.ceil(rows.length / itemsPerPage);
        let currentPage = 1;

        const showPage = (page) => {
            const start = (page - 1) * itemsPerPage;
            const end = start + itemsPerPage;

            rows.forEach((row, index) => {
                row.style.display = (index >= start && index < end) ? '' : 'none';
            });

            this.updatePaginationControls(pagination, currentPage, totalPages);
        };

        showPage(1);

        // Pagination controls
        pagination.addEventListener('click', (e) => {
            if (e.target.classList.contains('page-link')) {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page && page !== currentPage && page >= 1 && page <= totalPages) {
                    currentPage = page;
                    showPage(currentPage);
                }
            }
        });
    }

    updatePaginationControls(pagination, currentPage, totalPages) {
        const controls = pagination.querySelector('.pagination-controls');
        if (!controls) return;

        controls.innerHTML = `
            <button class="page-link" data-page="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i>
            </button>
            <span class="page-info">Page ${currentPage} of ${totalPages}</span>
            <button class="page-link" data-page="${currentPage + 1}" ${currentPage === totalPages ? 'disabled' : ''}>
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
    }

    // Chart Components
    createChart(canvasId, type, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        return new Chart(ctx, {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                ...options
            }
        });
    }

    // Form Components
    setupFormValidation() {
        document.querySelectorAll('form[data-validate]').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
        });
    }

    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'This field is required');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });

        return isValid;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        field.classList.add('error');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('error');
        const errorDiv = field.parentNode.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
}

// Initialize components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.components = new Components();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Components;
} 