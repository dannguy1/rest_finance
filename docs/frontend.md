# Frontend Specification - Garlic and Chives

## Overview

The frontend of Garlic and Chives is built using FastAPI with Jinja2 templates for server-side rendering, Bootstrap 5.3.6 for styling, and vanilla JavaScript for client-side interactions. The design focuses on a modern, responsive interface with real-time processing updates, intuitive data visualization, and an enhanced source mapping system with persistent metadata management.

## Technology Stack

### Core Technologies
- **Server-Side Rendering**: FastAPI with Jinja2 templates
- **UI Framework**: Bootstrap 5.3.6
- **Icons**: Bootstrap Icons
- **Charts**: Chart.js for data visualization
- **JavaScript**: Vanilla JavaScript (ES6+)
- **Real-time**: WebSocket for live updates
- **CSS**: Custom CSS with Bootstrap variables

### Key Features
- Responsive design with mobile-first approach
- Dark-themed navigation with off-canvas sidebar
- Source-specific drag & drop upload zones
- Real-time processing status updates
- Interactive data tables and charts
- Progressive enhancement with JavaScript
- Comprehensive error handling with retry mechanisms
- Accessibility compliance (WCAG 2.1 AA)
- Progressive Web App (PWA) capabilities
- Offline functionality for basic operations
- **Enhanced Source Mapping Modal** with metadata auto-loading and settings restore
- **Persistent Metadata Management** with sample data upload and processing
- **Multi-Level Validation** using saved metadata for input validation

## Template Architecture

### Directory Structure
```
app/templates/
├── base.html                 # Main layout template with navigation
├── source.html               # Source-specific application page
├── mapping.html              # Enhanced source mapping modal
├── pages/                    # Page-specific templates
│   ├── dashboard.html        # Main dashboard page
│   ├── upload.html           # File upload page
│   ├── process.html          # Data processing page
│   ├── analytics.html        # Data analytics page
│   ├── download.html         # Download page
│   ├── settings.html         # Settings page
│   └── index.html            # Landing page
├── components/               # Reusable UI components
└── partials/                 # Template partials
```

### Base Template Structure
```html
<!-- base.html - Main layout template -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Garlic and Chives - Financial Data Processor">
    <title>{% block title %}Garlic and Chives{% endblock %}</title>
    
    <!-- Favicon with embedded SVG -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%232563eb'><path d='M2.97 1.35A1 1 0 0 1 3.73 1h8.54a1 1 0 0 1 .76.35l2.609 3.044A1.5 1.5 0 0 1 16 5.37v.255a2.375 2.375 0 0 1-4.25 1.458A2.371 2.371 0 0 1 9.875 8 2.37 2.37 0 0 1 8 7.083 2.37 2.37 0 0 1 6.125 8a2.37 2.37 0 0 1-1.875-.917A2.375 2.375 0 0 1 0 5.625V5.37a1.5 1.5 0 0 1 .361-.976l2.61-3.045zm1.78 4.275a1.375 1.375 0 0 0 2.75 0 .5.5 0 0 1 1 0 1.375 1.375 0 0 0 2.75 0 .5.5 0 0 1 1 0 1.375 1.375 0 1 1-2.75 0 .5.5 0 0 1-1 0 1.375 1.375 0 1 1-2.75 0 .5.5 0 0 1-1 0zM1.5 9.5a.5.5 0 0 1 .5-.5h12a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-12a.5.5 0 0 1-.5-.5v-1zM1.5 11.5a.5.5 0 0 1 .5-.5h12a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-12a.5.5 0 0 1-.5-.5v-1zM1.5 13.5a.5.5 0 0 1 .5-.5h12a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-12a.5.5 0 0 1-.5-.5v-1z"/></svg>">
    
    <!-- Bootstrap CSS and Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Chart.js for data visualization -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="/static/css/main.css">
    <link rel="stylesheet" href="/static/css/components.css">
</head>
<body>
    <div class="d-flex flex-column min-vh-100">
        <!-- Top Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
            <div class="container-fluid">
                <button class="btn btn-dark me-3" id="sidebarToggle" type="button">
                    <i class="bi bi-list"></i>
                </button>
                
                <a class="navbar-brand" href="/">
                    <i class="bi bi-shop me-2"></i>
                    Garlic and Chives
                </a>
                
                <!-- Notifications dropdown -->
                <div class="navbar-nav ms-auto">
                    <div class="nav-item dropdown">
                        <button class="btn btn-dark dropdown-toggle" type="button" id="notificationsDropdown" data-bs-toggle="dropdown">
                            <i class="bi bi-bell"></i>
                            <span class="badge bg-danger" id="notification-badge">0</span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end" id="notifications-menu">
                            <li><h6 class="dropdown-header">Notifications</h6></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="#">No notifications</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </nav>
        
        <!-- Main Content -->
        <main class="flex-grow-1">
            <div class="container-fluid py-4">
                {% block content %}{% endblock %}
            </div>
        </main>
    </div>
    
    <!-- Off-Canvas Sidebar -->
    <div class="offcanvas offcanvas-start bg-dark text-light" id="sidebar" tabindex="-1">
        <div class="offcanvas-header border-bottom border-secondary">
            <h5 class="offcanvas-title">Navigation</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"></button>
        </div>
        
        <div class="offcanvas-body">
            <nav class="sidebar-nav">
                <ul class="nav flex-column">
                    <!-- Dashboard -->
                    <li class="nav-item">
                        <a class="nav-link text-light mb-2" href="/" data-page="dashboard">
                            <i class="bi bi-speedometer2 me-2"></i>
                            Dashboard
                        </a>
                    </li>
                    
                    <!-- Bank Statements Section -->
                    <li class="nav-item">
                        <h6 class="text-light-50 text-uppercase small mb-2 px-3">
                            <i class="bi bi-bank me-2"></i>
                            Bank Statements
                        </h6>
                        
                        <div class="nav-item">
                            <a class="nav-link text-light-50 mb-1 px-3" href="/source/bankofamerica" data-page="source-boa">
                                <i class="bi bi-bank me-2"></i>
                                Bank of America
                            </a>
                        </div>
                        
                        <div class="nav-item">
                            <a class="nav-link text-light-50 mb-1 px-3" href="/source/chase" data-page="source-chase">
                                <i class="bi bi-credit-card me-2"></i>
                                Chase
                            </a>
                        </div>
                    </li>
                    
                    <!-- Supplier Receipts Section -->
                    <li class="nav-item">
                        <h6 class="text-light-50 text-uppercase small mb-2 px-3">
                            <i class="bi bi-receipt me-2"></i>
                            Supplier Receipts
                        </h6>
                        
                        <div class="nav-item">
                            <a class="nav-link text-light-50 mb-1 px-3" href="/source/sysco" data-page="source-sysco">
                                <i class="bi bi-truck me-2"></i>
                                Sysco
                            </a>
                        </div>
                        
                        <div class="nav-item">
                            <a class="nav-link text-light-50 mb-1 px-3" href="/source/restaurantdepot" data-page="source-restaurantdepot">
                                <i class="bi bi-shop me-2"></i>
                                Restaurant Depot
                            </a>
                        </div>
                    </li>
                    
                    <!-- System Section -->
                    <li class="nav-item">
                        <h6 class="text-light-50 text-uppercase small mb-2 px-3">
                            <i class="bi bi-gear me-2"></i>
                            System
                        </h6>
                        
                        <a class="nav-link text-light-50 mb-1 px-3" href="/mapping" data-page="mapping">
                            <i class="bi bi-gear-wide-connected me-2"></i>
                            Source Mapping
                        </a>
                        
                        <a class="nav-link text-light-50 mb-1 px-3" href="/analytics" data-page="analytics">
                            <i class="bi bi-graph-up me-2"></i>
                            Analytics
                        </a>
                        
                        <a class="nav-link text-light-50 mb-1 px-3" href="/settings" data-page="settings">
                            <i class="bi bi-gear-wide-connected me-2"></i>
                            Settings
                        </a>
                    </li>
                </ul>
            </nav>
        </div>
    </div>

    <!-- Loading Overlay -->
    <div id="loading-overlay" class="loading-overlay" style="display: none;">
        <div class="loading-spinner">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p id="loading-message" class="mt-3">Processing...</p>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Custom JavaScript -->
    <script src="/static/js/main.js"></script>
    <script src="/static/js/components.js"></script>
    <script src="/static/js/api.js"></script>
    <script src="/static/js/utils.js"></script>
    
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

## Enhanced Source Mapping Modal

### Key Features
- **Auto-Loading Metadata**: Existing metadata automatically loads when source ID is entered
- **Always-On Dropdowns**: Source columns use dropdowns with common column names as defaults
- **Settings Restore**: Full configuration backup and restore including sample data
- **Sample Data Upload**: Upload and process sample files to generate metadata
- **Balanced UI Layout**: Professional 2-column layout for better organization
- **Multi-Level Validation**: Comprehensive validation using saved metadata

### Modal Workflow
1. **Source ID Entry**: Auto-loads existing metadata if available
2. **Sample Data Upload**: Upload sample file to generate metadata (required for new sources)
3. **Metadata Generation**: Process sample file to extract column information
4. **Mapping Configuration**: Configure column mappings using dropdowns
5. **Validation**: Real-time validation against sample data
6. **Save/Restore**: Save all settings or restore previous configuration

### UI Components
- **Basic Information Section**: 2-column balanced layout for source details
- **Column Mapping Table**: Editable table with source column dropdowns and target field inputs
- **Sample Data Section**: Upload and process sample files for metadata generation
- **Settings Restore**: Button to restore last saved configuration
- **Validation Feedback**: Real-time validation results and error messages

For detailed modal design guidelines, see `docs/modal_guidelines.md`.

## Source-Specific Pages

### Source Page Template
```html
<!-- source.html - Source-specific application page -->
{% extends "base.html" %}

{% block title %}{{ source_name }} - Garlic and Chives{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h1 class="h3 mb-1">
                    <i class="bi bi-{{ source_icon }} me-2"></i>
                    {{ source_name }}
                </h1>
                <p class="text-muted mb-0">{{ source_description }}</p>
            </div>
            <div class="btn-group" role="group">
                <button type="button" class="btn btn-outline-primary" data-bs-toggle="modal" data-bs-target="#uploadModal">
                    <i class="bi bi-cloud-upload me-2"></i>
                    Upload Files
                </button>
                <button type="button" class="btn btn-primary" id="processAllBtn">
                    <i class="bi bi-gear me-2"></i>
                    Process All Files
                </button>
            </div>
        </div>
    </div>
</div>

<!-- File Management Tabs -->
<div class="row">
    <div class="col-12">
        <ul class="nav nav-tabs" id="fileTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="upload-tab" data-bs-toggle="tab" data-bs-target="#upload" type="button" role="tab">
                    <i class="bi bi-cloud-upload me-2"></i>
                    Upload Files
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="process-tab" data-bs-toggle="tab" data-bs-target="#process" type="button" role="tab">
                    <i class="bi bi-gear me-2"></i>
                    Process Files
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="preview-tab" data-bs-toggle="tab" data-bs-target="#preview" type="button" role="tab">
                    <i class="bi bi-eye me-2"></i>
                    Preview Files
                </button>
            </li>
        </ul>
        
        <div class="tab-content" id="fileTabsContent">
            <!-- Upload Tab -->
            <div class="tab-pane fade show active" id="upload" role="tabpanel">
                <div class="card mt-3">
                    <div class="card-body">
                        <div class="drop-zone" id="dropZone">
                            <div class="drop-zone-content">
                                <i class="bi bi-cloud-upload fs-1 text-muted mb-3"></i>
                                <p class="text-muted">Drag & drop CSV files here</p>
                                <p class="text-muted small">or click to browse</p>
                            </div>
                            <input type="file" id="fileInput" multiple accept=".csv" style="display: none;">
                        </div>
                        <div class="progress mt-3" id="uploadProgress" style="display: none;">
                            <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Process Tab -->
            <div class="tab-pane fade" id="process" role="tabpanel">
                <div class="card mt-3">
                    <div class="card-body">
                        <div id="fileList">
                            <!-- File list will be populated by JavaScript -->
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Preview Tab -->
            <div class="tab-pane fade" id="preview" role="tabpanel">
                <div class="card mt-3">
                    <div class="card-body">
                        <div id="previewContent">
                            <!-- Preview content will be populated by JavaScript -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Upload Modal -->
<div class="modal fade" id="uploadModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Upload Files</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="drop-zone" id="modalDropZone">
                    <div class="drop-zone-content">
                        <i class="bi bi-cloud-upload fs-1 text-muted mb-3"></i>
                        <p class="text-muted">Drag & drop CSV files here</p>
                        <p class="text-muted small">or click to browse</p>
                    </div>
                    <input type="file" id="modalFileInput" multiple accept=".csv" style="display: none;">
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script src="/static/js/source.js"></script>
<script>
    // Initialize source page
    document.addEventListener('DOMContentLoaded', function() {
        const sourcePage = new SourcePage('{{ source }}');
        sourcePage.init();
    });
</script>
{% endblock %}
```

## JavaScript Architecture

### Directory Structure
```
app/static/js/
├── main.js                   # Main application logic
├── components.js             # Reusable UI components
├── api.js                    # API communication layer
├── utils.js                  # Utility functions
├── source.js                 # Source-specific functionality
└── components/               # Component-specific JavaScript
```

### Main Application Logic
```javascript
// main.js - Main application logic
class AppManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupSidebarToggle();
        this.setupGlobalEventListeners();
        this.setupNotifications();
    }
    
    setupSidebarToggle() {
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = new bootstrap.Offcanvas(document.getElementById('sidebar'));
        
        sidebarToggle.addEventListener('click', function() {
            sidebar.show();
        });
    }
    
    setupGlobalEventListeners() {
        // Handle navigation highlighting
        document.addEventListener('DOMContentLoaded', () => {
            this.highlightCurrentPage();
        });
    }
    
    setupNotifications() {
        // Initialize notification system
        this.notificationManager = new NotificationManager();
    }
    
    highlightCurrentPage() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link[data-page]');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }
}

// Initialize app manager
const appManager = new AppManager();
```

### Mapping Manager Implementation
```javascript
// Enhanced MappingManager for source mapping modal
class MappingManager {
    constructor() {
        this.currentMapping = null;
        this.availableSourceColumns = [];
        this.lastSavedSettings = null;
        this.init();
    }
    
    init() {
        this.loadMappings();
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Auto-load metadata when source ID changes
        const sourceIdInput = document.getElementById('sourceId');
        if (sourceIdInput) {
            sourceIdInput.addEventListener('blur', async () => {
                await this.loadMetadataForSourceId();
            });
        }
        
        // Handle custom column selection
        document.addEventListener('change', (e) => {
            if (e.target.tagName === 'SELECT' && e.target.value === 'custom') {
                this.handleCustomColumnSelection(e.target);
            }
        });
    }
    
    async loadMetadataForSourceId() {
        const sourceId = document.getElementById('sourceId').value;
        if (!sourceId) return;
        
        try {
            const response = await fetch(`/api/sample-data/sources/${sourceId}/metadata`);
            if (response.ok) {
                const metadata = await response.json();
                this.availableSourceColumns = metadata.columns || [];
                this.populateSourceColumnDropdowns();
            }
        } catch (error) {
            console.log('No existing metadata found for source ID');
        }
    }
    
    populateSourceColumnDropdowns() {
        const sourceColumnSelects = document.querySelectorAll('.source-column-select');
        sourceColumnSelects.forEach(select => {
            select.innerHTML = '';
            
            // Add common column names as defaults
            const commonColumns = ['Date', 'Description', 'Amount', 'Type', 'Status', 'Balance'];
            const allColumns = [...new Set([...this.availableSourceColumns, ...commonColumns])];
            
            allColumns.forEach(column => {
                const option = document.createElement('option');
                option.value = column;
                option.textContent = column;
                select.appendChild(option);
            });
            
            // Add custom option
            const customOption = document.createElement('option');
            customOption.value = 'custom';
            customOption.textContent = 'Custom...';
            select.appendChild(customOption);
        });
    }
    
    async processSampleFile() {
        const fileInput = document.getElementById('sampleDataFile');
        const file = fileInput.files[0];
        
        if (!file) {
            utils.showError('Please select a sample file');
            return;
        }
        
        const sourceId = document.getElementById('sourceId').value;
        if (!sourceId) {
            utils.showError('Please enter a Source ID first');
            return;
        }
        
        try {
            utils.showLoading('Processing sample file...');
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`/api/sample-data/process/${sourceId}`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.availableSourceColumns = result.columns || [];
                this.populateSourceColumnDropdowns();
                utils.showSuccess('Sample file processed successfully');
            } else {
                throw new Error('Failed to process sample file');
            }
        } catch (error) {
            utils.showError('Processing failed: ' + error.message);
        } finally {
            utils.hideLoading();
        }
    }
    
    async saveMapping() {
        const mapping = this.collectMappingData();
        
        try {
            utils.showLoading('Saving mapping...');
            
            const response = await fetch('/api/mappings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(mapping)
            });
            
            if (response.ok) {
                this.lastSavedSettings = mapping;
                utils.showSuccess('Mapping saved successfully');
            } else {
                throw new Error('Failed to save mapping');
            }
        } catch (error) {
            utils.showError('Save failed: ' + error.message);
        } finally {
            utils.hideLoading();
        }
    }
    
    async restoreSettings() {
        if (!this.lastSavedSettings) {
            utils.showError('No saved settings to restore');
            return;
        }
        
        try {
            utils.showLoading('Restoring settings...');
            this.populateFormWithMapping(this.lastSavedSettings);
            utils.showSuccess('Settings restored successfully');
        } catch (error) {
            utils.showError('Restore failed: ' + error.message);
        } finally {
            utils.hideLoading();
        }
    }
    
    collectMappingData() {
        // Collect all form data including sample data
        const mapping = {
            source_id: document.getElementById('sourceId').value,
            display_name: document.getElementById('displayName').value,
            description: document.getElementById('description').value,
            icon: document.getElementById('icon').value,
            // ... other mapping fields
            example_data: this.getSampleData()
        };
        
        return mapping;
    }
    
    getSampleData() {
        // Extract sample data from the form
        // This would be the processed sample data
        return this.lastProcessedSampleData || [];
    }
}
```

### API Communication Layer
```javascript
// api.js - API communication layer
class API {
    static async request(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    // File management endpoints
    static async uploadFiles(source, files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        
        return await this.request(`/api/files/upload/${source}`, {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    }
    
    static async getFileList(source) {
        return await this.request(`/api/files/list/${source}`);
    }
    
    static async deleteFile(source, filename) {
        return await this.request(`/api/files/${source}/${filename}`, {
            method: 'DELETE'
        });
    }
    
    static async getFilePreview(source, filename) {
        return await this.request(`/api/files/preview-uploaded/${source}?file=${filename}`);
    }
    
    static async getFilePreviewFull(source, filename) {
        return await this.request(`/api/files/preview-uploaded-full/${source}?file=${filename}`);
    }
    
    // Processing endpoints
    static async processFile(source, filename, options = {}) {
        return await this.request(`/api/files/process/${source}/${filename}`, {
            method: 'POST',
            body: JSON.stringify(options)
        });
    }
    
    static async processAllFiles(source, year, options = {}) {
        return await this.request(`/api/processing/process/${source}/${year}`, {
            method: 'POST',
            body: JSON.stringify(options)
        });
    }
    
    // Output file endpoints
    static async getOutputFiles(source, year = null) {
        const url = year ? 
            `/api/files/output/${source}?year=${year}` : 
            `/api/files/output/${source}`;
        return await this.request(url);
    }
    
    static async downloadOutputFile(source, year, month) {
        window.open(`/api/processing/download/${source}/${year}/${month}`, '_blank');
    }
    
    static async deleteOutputFile(source, year, month) {
        return await this.request(`/api/files/processed/${source}/${year}/${month}`, {
            method: 'DELETE'
        });
    }
    
    // Sample data and metadata endpoints
    static async uploadSampleData(sourceId, file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return await this.request(`/api/sample-data/upload/${sourceId}`, {
            method: 'POST',
            body: formData,
            headers: {}
        });
    }
    
    static async processSampleData(sourceId) {
        return await this.request(`/api/sample-data/process/${sourceId}`, {
            method: 'POST'
        });
    }
    
    static async getMetadata(sourceId) {
        return await this.request(`/api/sample-data/sources/${sourceId}/metadata`);
    }
    
    static async validateFileAgainstMetadata(sourceId, file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return await this.request(`/api/sample-data/sources/${sourceId}/validate`, {
            method: 'POST',
            body: formData,
            headers: {}
        });
    }
    
    // Mapping endpoints
    static async getMappings() {
        return await this.request('/api/mappings');
    }
    
    static async getMapping(sourceId) {
        return await this.request(`/api/mappings/${sourceId}`);
    }
    
    static async saveMapping(mapping) {
        return await this.request('/api/mappings', {
            method: 'POST',
            body: JSON.stringify(mapping)
        });
    }
    
    static async updateMapping(sourceId, mapping) {
        return await this.request(`/api/mappings/${sourceId}`, {
            method: 'PUT',
            body: JSON.stringify(mapping)
        });
    }
    
    static async deleteMapping(sourceId) {
        return await this.request(`/api/mappings/${sourceId}`, {
            method: 'DELETE'
        });
    }
    
    static async validateMapping(sourceId, mapping) {
        return await this.request(`/api/mappings/${sourceId}/validate`, {
            method: 'POST',
            body: JSON.stringify(mapping)
        });
    }
}
```

### Utility Functions
```javascript
// utils.js - Utility functions
const utils = {
    async apiCall(endpoint, options = {}) {
        return await API.request(endpoint, options);
    },
    
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');
        if (overlay) {
            if (messageEl) messageEl.textContent = message;
            overlay.style.display = 'flex';
        }
    },
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    },
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    },
    
    showError(message) {
        this.showAlert(message, 'danger');
    },
    
    showWarning(message) {
        this.showAlert(message, 'warning');
    },
    
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer') || this.createAlertContainer();
        
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" id="${alertId}" role="alert">
                <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    },
    
    createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    },
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};
```

## CSS Design System

### Design Tokens
```css
:root {
  /* Color Palette */
  --bs-primary: #2563eb;
  --bs-success: #16a34a;
  --bs-warning: #ca8a04;
  --bs-danger: #dc2626;
  --bs-info: #0891b2;
  --bs-secondary: #64748b;
  
  /* Typography */
  --font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 3rem;
  
  /* Shadows */
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.15);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.2);
  
  /* Border Radius */
  --border-radius-sm: 0.25rem;
  --border-radius: 0.375rem;
  --border-radius-lg: 0.5rem;
  
  /* Transitions */
  --transition-fast: 0.15s ease-in-out;
  --transition-normal: 0.2s ease-in-out;
  --transition-slow: 0.3s ease-in-out;
}
```

### Drag-Drop Zone Styling
```css
/* Drag-Drop Zone Styling */
.drop-zone {
  border: 2px dashed #dee2e6;
  border-radius: var(--border-radius);
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-normal);
  background-color: #f8f9fa;
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-zone:hover {
  border-color: var(--bs-primary);
  background-color: rgba(37, 99, 235, 0.05);
}

.drop-zone.drag-over {
  border-color: var(--bs-primary);
  background-color: rgba(37, 99, 235, 0.1);
  transform: scale(1.02);
}

.drop-zone-content {
  pointer-events: none;
}

.drop-zone-content i {
  transition: all var(--transition-normal);
}

.drop-zone:hover .drop-zone-content i,
.drop-zone.drag-over .drop-zone-content i {
  color: var(--bs-primary) !important;
  transform: scale(1.1);
}
```

### Loading Overlay
```css
/* Loading Overlay */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-spinner {
  background-color: white;
  padding: 2rem;
  border-radius: var(--border-radius-lg);
  text-align: center;
  box-shadow: var(--shadow-lg);
}

.loading-spinner .spinner-border {
  width: 3rem;
  height: 3rem;
}
```

## Responsive Design

### Breakpoint Strategy
- **Mobile First**: Design starts with mobile and scales up
- **Bootstrap Breakpoints**: xs (<576px), sm (≥576px), md (≥768px), lg (≥992px), xl (≥1200px)
- **Flexible Grid**: Bootstrap grid system for responsive layouts
- **Touch-Friendly**: Minimum 44px touch targets for mobile

### Mobile Optimizations
- Collapsible sidebar for navigation
- Simplified upload zones on small screens
- Touch-friendly buttons and controls
- Optimized table layouts with horizontal scrolling
- Reduced animations for better performance

## Performance Considerations

### Frontend Optimization
- **Lazy Loading**: Load components on demand
- **Virtual Scrolling**: Handle large data tables efficiently
- **Debounced Search**: Optimize search performance
- **Memoization**: Cache expensive calculations
- **Image Optimization**: Compress and optimize images
- **Minification**: Minify CSS and JavaScript in production

### Loading States
- Skeleton screens for better perceived performance
- Progressive loading of data
- Optimistic UI updates
- Graceful degradation for slow connections

## Accessibility

### WCAG Compliance
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Proper ARIA labels and roles
- **Color Contrast**: Minimum 4.5:1 contrast ratio
- **Focus Management**: Clear focus indicators
- **Error Handling**: Descriptive error messages

### Accessibility Features
- Skip navigation links
- Proper heading hierarchy
- Alt text for images
- Form labels and descriptions
- Error announcements for screen readers

## Browser Support

### Supported Browsers
- **Chrome**: Latest 2 versions
- **Firefox**: Latest 2 versions
- **Safari**: Latest 2 versions
- **Edge**: Latest 2 versions

### Progressive Enhancement
- Core functionality works without JavaScript
- Enhanced features with JavaScript enabled
- Graceful degradation for older browsers
- Feature detection for advanced capabilities

## Testing Strategy

### Frontend Testing
- **Manual Testing**: Cross-browser testing
- **Automated Testing**: Selenium for critical user flows
- **Accessibility Testing**: axe-core for WCAG compliance
- **Performance Testing**: Lighthouse for performance audits
- **Mobile Testing**: Device testing and responsive validation

### Testing Tools
- **Selenium WebDriver**: Automated browser testing
- **axe-core**: Accessibility testing
- **Lighthouse**: Performance and best practices
- **BrowserStack**: Cross-browser testing
- **Jest**: Unit testing for JavaScript utilities

## Deployment Considerations

### Build Process
- **Asset Optimization**: Minify and compress static assets
- **Template Compilation**: Pre-compile Jinja2 templates
- **Static File Serving**: Configure proper caching headers
- **CDN Integration**: Use CDN for static assets in production

### Environment Configuration
- **Development**: Hot reloading and debug tools
- **Staging**: Production-like environment for testing
- **Production**: Optimized builds with monitoring

## Privacy Protection

### Data Handling
- **User Data Isolation**: All user data stored separately from source code
- **No Frontend Exposure**: User data never sent to frontend except for preview/restore
- **Secure Processing**: Protected file processing and storage
- **Configuration Privacy**: Actual configurations excluded from version control

### Security Features
- **Input Validation**: Comprehensive client-side and server-side validation
- **File Type Restrictions**: Strict file type validation
- **Size Limits**: File size restrictions and malicious file detection
- **Path Traversal Prevention**: Secure file handling

## Future Enhancements

### UI/UX Improvements
1. **Dark/Light Theme Toggle**: User preference for theme switching
2. **Customizable Dashboard**: Drag-and-drop dashboard widgets
3. **Advanced Filtering**: Multi-criteria search and filtering
4. **Export Options**: PDF reports and data export
5. **Mobile App**: Progressive Web App (PWA) capabilities

### Technical Improvements
1. **Component Library**: Reusable UI component system
2. **State Management**: Centralized state management
3. **TypeScript Migration**: Type safety for JavaScript
4. **Build System**: Modern build tools (Vite, Webpack)
5. **Testing Framework**: Comprehensive testing suite

---

For detailed backend API design and data processing logic, see `backend.md`. For source mapping system details, see `mapping_technical_spec.md` and `mapping_design.md`. For modal dialog guidelines, see `modal_guidelines.md`. 