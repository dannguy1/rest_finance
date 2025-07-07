// Source Application JavaScript - v1.1
// Updated: 2025-07-03 - Added delete functionality and tooltips
class SourceApp {
    constructor() {
        this.config = window.sourceConfig;
        this.currentFile = null;
        console.log('SourceApp initializing with config:', this.config);
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFileUpload();
        this.setupTabEvents();
        this.setupFileManagement();
        this.setupFilters();
        this.setupPreviewTab();
        this.loadProcessedFiles();
    }

    setupEventListeners() {
        // File upload events
        this.setupFileUpload();
        
        // Tab events
        this.setupTabEvents();
        
        // File management events
        this.setupFileManagement();
        
        // Filter events
        this.setupFilters();
    }

    setupFileUpload() {
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('file-input');
        const browseBtn = document.getElementById('browse-files-btn');

        // Browse button click
        if (browseBtn) {
            browseBtn.addEventListener('click', () => {
                fileInput.click();
            });
        }

        // File input change
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFiles(Array.from(e.target.files));
            });
        }

        // Drag and drop events
        if (uploadZone) {
            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.classList.add('drag-over');
            });

            uploadZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('drag-over');
            });

            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('drag-over');
                const files = Array.from(e.dataTransfer.files);
                this.handleFiles(files);
            });

            uploadZone.addEventListener('click', () => {
                fileInput.click();
            });
        }
    }

    setupTabEvents() {
        // Handle tab changes
        const tabs = document.querySelectorAll('#sourceTabs button[data-bs-toggle="tab"]');
        tabs.forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                if (e.target.id === 'files-tab') {
                    this.loadProcessedFiles();
                } else if (e.target.id === 'upload-tab') {
                    this.loadUploadedFiles();
                } else if (e.target.id === 'preview-tab') {
                    this.populatePreviewFileDropdown();
                }
            });
        });
    }

    setupFileManagement() {
        // Refresh files button
        const refreshBtn = document.getElementById('refresh-files-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadProcessedFiles();
            });
        }

        // Check files button
        const checkFilesBtn = document.getElementById('check-files-btn');
        if (checkFilesBtn) {
            checkFilesBtn.addEventListener('click', () => {
                this.checkFiles();
            });
        }

        // Download button in modal
        const downloadBtn = document.getElementById('download-file-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                if (this.currentFile) {
                    this.downloadFile(this.currentFile);
                }
            });
        }
    }

    setupFilters() {
        const yearFilter = document.getElementById('year-filter');
        const monthFilter = document.getElementById('month-filter');

        if (yearFilter) {
            yearFilter.addEventListener('change', () => {
                this.filterFiles();
            });
        }

        if (monthFilter) {
            monthFilter.addEventListener('change', () => {
                this.filterFiles();
            });
        }
    }

    async handleFiles(files) {
        const csvFiles = files.filter(file => 
            file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv')
        );

        if (csvFiles.length === 0) {
            this.showAlert('Please select valid CSV files', 'warning');
            return;
        }

        this.showUploadProgress();
        await this.uploadFiles(csvFiles);
    }

    async uploadFiles(files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch(`/api/files/upload/${this.config.source}`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.showAlert(`${files.length} files uploaded successfully`, 'success');
                this.hideUploadProgress();
                this.showUploadedFiles(result.files);
                
                // Switch to files tab after successful upload
                setTimeout(() => {
                    const filesTab = document.getElementById('files-tab');
                    if (filesTab) {
                        const tab = new bootstrap.Tab(filesTab);
                        tab.show();
                    }
                }, 2000);
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            this.showAlert('Upload failed: ' + error.message, 'danger');
            this.hideUploadProgress();
        }
    }

    showUploadProgress() {
        const progress = document.getElementById('upload-progress');
        if (progress) {
            progress.style.display = 'block';
        }
    }

    hideUploadProgress() {
        const progress = document.getElementById('upload-progress');
        if (progress) {
            progress.style.display = 'none';
        }
    }

    showUploadedFiles(files) {
        const container = document.getElementById('uploaded-files');
        const tbody = document.getElementById('uploaded-files-body');
        
        if (container && tbody) {
            container.style.display = 'block';
            tbody.innerHTML = '';
            
            files.forEach(file => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <i class="bi bi-file-earmark-text me-2"></i>
                        ${file.name}
                    </td>
                    <td>${this.formatFileSize(file.size || 0)}</td>
                    <td>${this.formatDate(new Date())}</td>
                    <td><span class="badge bg-success rounded-pill">Uploaded</span></td>
                    <td>
                        <div class="btn-group btn-group-sm" role="group">
                            <button type="button" class="btn btn-outline-info" title="Verify input data" onclick="sourceApp.analyzeFile('${file.name}')">
                                <i class="bi bi-search"></i>
                            </button>
                            <button type="button" class="btn btn-outline-primary" title="Preview CSV content" onclick="sourceApp.previewUploadedFile('${file.name}')">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button type="button" class="btn btn-outline-secondary" title="Analytics" onclick="sourceApp.analyzeUploadedFile('${file.name}')">
                                <i class="bi bi-graph-up"></i>
                            </button>
                            <button type="button" class="btn btn-outline-warning" title="Process only this file" onclick="sourceApp.processFile('${file.name}')">
                                <i class="bi bi-gear"></i>
                            </button>
                            <button type="button" class="btn btn-outline-danger" title="Delete this file" onclick="sourceApp.deleteFile('${file.name}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
            
            // Show/hide Process All Files button
            const processButton = document.getElementById('process-all-btn');
            if (files.length > 0 && processButton) {
                processButton.style.display = 'inline-block';
                processButton.onclick = () => this.processAllFiles();
            } else if (processButton) {
                processButton.style.display = 'none';
            }
        }
    }

    async loadProcessedFiles() {
        console.log('loadProcessedFiles called');
        try {
            const loadingState = document.getElementById('files-loading');
            console.log('Loading state element:', loadingState);
            if (loadingState) {
                loadingState.style.display = 'block';
            }

            console.log('Fetching from:', `/api/files/${this.config.source}`);
            const response = await fetch(`/api/files/${this.config.source}`);
            console.log('Response status:', response.status);
            if (response.ok) {
                const data = await response.json();
                console.log('Received data:', data);
                this.displayProcessedFiles(data.files);
            } else {
                throw new Error('Failed to load processed files');
            }
        } catch (error) {
            console.error('Error in loadProcessedFiles:', error);
            this.showAlert('Failed to load processed files', 'danger');
        } finally {
            const loadingState = document.getElementById('files-loading');
            if (loadingState) {
                loadingState.style.display = 'none';
            }
        }
    }

    displayProcessedFiles(files) {
        const treeContainer = document.getElementById('processed-files-tree');
        const emptyState = document.getElementById('empty-state');
        
        if (!treeContainer) {
            return;
        }

        if (files.length === 0) {
            treeContainer.innerHTML = '';
            if (emptyState) {
                emptyState.style.display = 'block';
            }
            return;
        }

        if (emptyState) {
            emptyState.style.display = 'none';
        }

        // Group files by year
        const filesByYear = {};
        files.forEach(file => {
            if (!filesByYear[file.year]) {
                filesByYear[file.year] = [];
            }
            filesByYear[file.year].push(file);
        });

        // Sort years in descending order
        const sortedYears = Object.keys(filesByYear).sort((a, b) => b - a);

        treeContainer.innerHTML = '';
        
        sortedYears.forEach(year => {
            const yearFiles = filesByYear[year];
            
            // Create year folder
            const yearFolder = document.createElement('div');
            yearFolder.className = 'tree-item folder';
            yearFolder.style.display = 'flex';
            yearFolder.style.alignItems = 'center';
            yearFolder.style.flexWrap = 'nowrap';
            yearFolder.style.width = '100%';
            yearFolder.innerHTML = `
                <span class="tree-indent" style="width: 1.5rem; display: inline-block; flex-shrink: 0;"></span>
                <i class="bi bi-chevron-right tree-toggle" style="cursor: pointer; color: #6c757d; transition: transform 0.2s; flex-shrink: 0;" onclick="sourceApp.toggleFolder(this)"></i>
                <i class="bi bi-folder-fill tree-icon folder" style="width: 1.2rem; margin-right: 0.5rem; text-align: center; flex-shrink: 0; color: #ffc107;"></i>
                <span class="tree-name" style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 0.5rem; min-width: 0;">${year}</span>
                <span class="text-muted small">(${yearFiles.length} files)</span>
            `;
            treeContainer.appendChild(yearFolder);

            // Create children container
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'tree-children';
            treeContainer.appendChild(childrenContainer);

            // Sort files by month
            yearFiles.sort((a, b) => a.month - b.month).forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'tree-item file';
                fileItem.style.display = 'flex';
                fileItem.style.alignItems = 'center';
                fileItem.style.flexWrap = 'nowrap';
                fileItem.style.width = '100%';
                fileItem.innerHTML = `
                    <span class="tree-indent" style="width: 1.5rem; display: inline-block; flex-shrink: 0;"></span>
                    <span class="tree-indent" style="width: 1.5rem; display: inline-block; flex-shrink: 0;"></span>
                    <i class="bi bi-file-earmark-text tree-icon file" style="width: 1.2rem; margin-right: 0.5rem; text-align: center; flex-shrink: 0;"></i>
                    <span class="tree-name" style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 0.5rem; min-width: 0;">${file.name}</span>
                    <span class="text-muted small" style="margin-right: 1.5rem;">${this.formatFileSize(file.size)}</span>
                    <div class="tree-actions" style="display: flex; gap: 0.25rem; margin-left: auto; flex-shrink: 0; white-space: nowrap;">
                        <button type="button" class="btn btn-outline-primary btn-sm" title="Preview" onclick="sourceApp.previewFile('${file.path}')">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button type="button" class="btn btn-outline-info btn-sm" title="Analytics" onclick="sourceApp.analyzeFile('${file.path}')">
                            <i class="bi bi-graph-up"></i>
                        </button>
                        <button type="button" class="btn btn-outline-success btn-sm" title="Download" onclick="sourceApp.downloadFile('${file.path}')">
                            <i class="bi bi-download"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger btn-sm" title="Delete" onclick="sourceApp.deleteProcessedFile(${file.year}, ${parseInt(file.month, 10)})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                `;
                childrenContainer.appendChild(fileItem);
                
                // Debug: Log the computed styles
                setTimeout(() => {
                    const computedStyle = window.getComputedStyle(fileItem);
                    console.log('File item display:', computedStyle.display);
                    console.log('File item flex-direction:', computedStyle.flexDirection);
                    console.log('File item HTML:', fileItem.outerHTML);
                }, 100);
            });
        });
    }

    toggleFolder(toggleElement) {
        const treeItem = toggleElement.closest('.tree-item');
        const childrenContainer = treeItem.nextElementSibling;
        
        if (childrenContainer && childrenContainer.classList.contains('tree-children')) {
            childrenContainer.classList.toggle('collapsed');
            toggleElement.classList.toggle('expanded');
        }
    }

    async previewFile(filePath) {
        console.log('previewFile called with:', filePath);
        
        // Switch to Preview tab
        const previewTab = document.getElementById('preview-tab');
        if (previewTab) {
            const tab = new bootstrap.Tab(previewTab);
            tab.show();
        }
        
        // Ensure dropdown is populated and then set the file
        await this.populatePreviewFileDropdown();
        
        // Set the file in the preview dropdown and load it
        const previewDropdown = document.getElementById('preview-file-select');
        if (previewDropdown) {
            // Find the option that matches this file path (processed files use "processed:path" format)
            const targetValue = `processed:${filePath}`;
            for (let option of previewDropdown.options) {
                if (option.value === targetValue) {
                    previewDropdown.value = targetValue;
                    // Trigger the change event to load the preview
                    previewDropdown.dispatchEvent(new Event('change'));
                    break;
                }
            }
        }
    }

    async downloadFile(filePath) {
        console.log('downloadFile called with:', filePath);
        try {
            const response = await fetch(`/api/files/download/${this.config.source}?file=${encodeURIComponent(filePath)}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filePath.split('/').pop();
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            this.showAlert('Download failed', 'danger');
        }
    }

    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the content
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    getMonthName(month) {
        const months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        return months[month - 1] || month;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        // Convert Unix timestamp (seconds) to milliseconds for JavaScript Date constructor
        const timestamp = typeof dateString === 'number' ? dateString * 1000 : dateString;
        return new Date(timestamp).toLocaleDateString();
    }

    async processAllFiles() {
        console.log('processAllFiles called');
        try {
            const currentYear = new Date().getFullYear();
            const response = await fetch(`/api/processing/process/${this.config.source}/${currentYear}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    include_source_file: true
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.showAlert(`All files processed successfully!`, 'success');
                
                // Refresh the uploaded files list
                this.loadUploadedFiles();
                
                // Switch to processed files tab after successful processing
                setTimeout(() => {
                    const filesTab = document.getElementById('files-tab');
                    if (filesTab) {
                        const tab = new bootstrap.Tab(filesTab);
                        tab.show();
                    }
                }, 2000);
            } else {
                throw new Error('Processing failed');
            }
        } catch (error) {
            this.showAlert('Processing failed: ' + error.message, 'danger');
        }
    }

    async processFile(filename) {
        console.log('processFile called with:', filename);
        try {
            const response = await fetch(`/api/files/process/${this.config.source}/${encodeURIComponent(filename)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    include_source_file: true
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.showAlert(`File ${filename} processed successfully!`, 'success');
                
                // Refresh the uploaded files list
                this.loadUploadedFiles();
                
                // Switch to processed files tab after successful processing
                setTimeout(() => {
                    const filesTab = document.getElementById('files-tab');
                    if (filesTab) {
                        const tab = new bootstrap.Tab(filesTab);
                        tab.show();
                    }
                }, 2000);
            } else {
                throw new Error('Processing failed');
            }
        } catch (error) {
            this.showAlert('Processing failed: ' + error.message, 'danger');
        }
    }

    async deleteFile(filename) {
        console.log('deleteFile called with:', filename);
        if (!confirm(`Are you sure you want to delete ${filename}?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/files/${this.config.source}/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showAlert(`File ${filename} deleted successfully`, 'success');
                this.loadUploadedFiles();
            } else {
                throw new Error('Delete failed');
            }
        } catch (error) {
            this.showAlert('Delete failed: ' + error.message, 'danger');
        }
    }

    async deleteProcessedFile(year, month) {
        console.log('deleteProcessedFile called with:', year, month);
        const monthName = this.getMonthName(month);
        if (!confirm(`Are you sure you want to delete the processed file for ${monthName} ${year}?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/files/processed/${this.config.source}/${year}/${month}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showAlert(`Processed file for ${monthName} ${year} deleted successfully`, 'success');
                this.loadProcessedFiles(); // Refresh the processed files list
            } else {
                throw new Error('Delete failed');
            }
        } catch (error) {
            this.showAlert('Delete failed: ' + error.message, 'danger');
        }
    }

    async loadUploadedFiles() {
        try {
            const response = await fetch(`/api/files/list/${this.config.source}`);
            if (response.ok) {
                const data = await response.json();
                this.showUploadedFiles(data.files);
            } else {
                throw new Error('Failed to load uploaded files');
            }
        } catch (error) {
            this.showAlert('Failed to load uploaded files', 'danger');
        }
    }

    async previewUploadedFile(filename) {
        console.log('previewUploadedFile called with:', filename);
        
        // Switch to Preview tab
        const previewTab = document.getElementById('preview-tab');
        if (previewTab) {
            const tab = new bootstrap.Tab(previewTab);
            tab.show();
        }
        
        // Ensure dropdown is populated and then set the file
        await this.populatePreviewFileDropdown();
        
        // Set the file in the preview dropdown and load it
        const previewDropdown = document.getElementById('preview-file-select');
        if (previewDropdown) {
            // Find the option that matches this filename (uploaded files use "uploaded:filename" format)
            const targetValue = `uploaded:${filename}`;
            for (let option of previewDropdown.options) {
                if (option.value === targetValue) {
                    previewDropdown.value = targetValue;
                    // Trigger the change event to load the preview
                    previewDropdown.dispatchEvent(new Event('change'));
                    break;
                }
            }
        }
    }

    setupPreviewTab() {
        // Setup file selection dropdown (hidden, used programmatically)
        const fileSelect = document.getElementById('preview-file-select');
        
        if (fileSelect) {
            // Auto-load preview when file is selected
            fileSelect.addEventListener('change', () => {
                if (fileSelect.value) {
                    this.loadFullPreview(fileSelect.value);
                } else {
                    // Clear preview when no file is selected
                    this.clearPreview();
                }
            });
        }
        
        // Setup download button
        const downloadBtn = document.getElementById('preview-download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadCurrentPreviewFile();
            });
        }
        
        // Setup sort controls
        this.setupPreviewSortControls();
        
        // Populate file dropdown
        this.populatePreviewFileDropdown();
    }

    setupPreviewSortControls() {
        // Setup event listeners for all three sort levels
        for (let level = 1; level <= 3; level++) {
            const sortColumn = document.getElementById(`preview-sort-column-${level}`);
            const sortAsc = document.getElementById(`preview-sort-asc-${level}`);
            const sortDesc = document.getElementById(`preview-sort-desc-${level}`);
            
            if (sortColumn) {
                sortColumn.addEventListener('change', () => {
                    this.updateSortDirectionButtons(level);
                });
            }
            
            if (sortAsc) {
                sortAsc.addEventListener('click', () => {
                    this.setSortDirection(level, 'asc');
                });
            }
            
            if (sortDesc) {
                sortDesc.addEventListener('click', () => {
                    this.setSortDirection(level, 'desc');
                });
            }
        }
        
        // Setup apply button
        const sortApply = document.getElementById('preview-sort-apply');
        if (sortApply) {
            sortApply.addEventListener('click', () => {
                this.applyPreviewSort();
            });
        }
        
        // Setup clear button
        const sortClear = document.getElementById('preview-sort-clear');
        if (sortClear) {
            sortClear.addEventListener('click', () => {
                this.clearPreviewSort();
            });
        }
    }

    updateSortDirectionButtons(level) {
        const sortColumn = document.getElementById(`preview-sort-column-${level}`);
        const sortAsc = document.getElementById(`preview-sort-asc-${level}`);
        const sortDesc = document.getElementById(`preview-sort-desc-${level}`);
        
        if (sortColumn && sortAsc && sortDesc) {
            const hasColumn = sortColumn.value !== '';
            sortAsc.disabled = !hasColumn;
            sortDesc.disabled = !hasColumn;
            
            // Reset button states
            sortAsc.classList.remove('active');
            sortDesc.classList.remove('active');
        }
    }

    setSortDirection(level, direction) {
        const sortAsc = document.getElementById(`preview-sort-asc-${level}`);
        const sortDesc = document.getElementById(`preview-sort-desc-${level}`);
        
        if (sortAsc && sortDesc) {
            sortAsc.classList.remove('active');
            sortDesc.classList.remove('active');
            
            if (direction === 'asc') {
                sortAsc.classList.add('active');
            } else {
                sortDesc.classList.add('active');
            }
        }
    }

    applyPreviewSort() {
        if (!this.currentPreviewData) return;
        
        // Collect all active sort criteria
        const sortCriteria = [];
        
        for (let level = 1; level <= 3; level++) {
            const sortColumn = document.getElementById(`preview-sort-column-${level}`);
            const sortAsc = document.getElementById(`preview-sort-asc-${level}`);
            
            if (sortColumn && sortColumn.value !== '') {
                const columnIndex = parseInt(sortColumn.value);
                const isAscending = sortAsc.classList.contains('active');
                
                sortCriteria.push({
                    columnIndex: columnIndex,
                    ascending: isAscending,
                    level: level
                });
            }
        }
        
        if (sortCriteria.length === 0) {
            // No sorting criteria, show original data
            this.displayPreviewTableWithData(this.currentPreviewData.headers, this.currentPreviewData.rows);
            return;
        }
        
        // Sort the data using all criteria
        const sortedRows = [...this.currentPreviewData.rows].sort((a, b) => {
            for (const criteria of sortCriteria) {
                const aVal = a[criteria.columnIndex] || '';
                const bVal = b[criteria.columnIndex] || '';
                
                // Try to parse as numbers for numeric sorting
                const aNum = parseFloat(aVal);
                const bNum = parseFloat(bVal);
                
                let comparison = 0;
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    comparison = aNum - bNum;
                } else {
                    // String comparison
                    comparison = aVal.toString().localeCompare(bVal.toString());
                }
                
                // Apply sort direction
                if (!criteria.ascending) {
                    comparison = -comparison;
                }
                
                // If this level has a difference, return it
                if (comparison !== 0) {
                    return comparison;
                }
                
                // If equal, continue to next sort level
            }
            
            return 0; // All criteria are equal
        });
        
        // Update the table with sorted data
        this.displayPreviewTableWithData(this.currentPreviewData.headers, sortedRows);
    }

    clearPreviewSort() {
        // Clear all sort selections
        for (let level = 1; level <= 3; level++) {
            const sortColumn = document.getElementById(`preview-sort-column-${level}`);
            const sortAsc = document.getElementById(`preview-sort-asc-${level}`);
            const sortDesc = document.getElementById(`preview-sort-desc-${level}`);
            
            if (sortColumn) {
                sortColumn.value = '';
            }
            
            if (sortAsc) {
                sortAsc.classList.remove('active');
                sortAsc.disabled = true;
            }
            
            if (sortDesc) {
                sortDesc.classList.remove('active');
                sortDesc.disabled = true;
            }
        }
        
        // Show original data
        if (this.currentPreviewData) {
            this.displayPreviewTableWithData(this.currentPreviewData.headers, this.currentPreviewData.rows);
        }
    }

    formatTableCell(cell, index, headers) {
        if (!cell) return '';
        
        const header = headers[index] ? headers[index].toLowerCase() : '';
        const value = cell.toString();
        
        // Format amounts (assuming amount columns contain numbers)
        if (header.includes('amount') || header.includes('total') || header.includes('sum')) {
            const num = parseFloat(value);
            if (!isNaN(num)) {
                return num.toLocaleString('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
        
        // Format dates
        if (header.includes('date')) {
            const date = new Date(value);
            if (!isNaN(date.getTime())) {
                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
            }
        }
        
        // Format large numbers
        const num = parseFloat(value);
        if (!isNaN(num) && Math.abs(num) >= 1000) {
            return num.toLocaleString('en-US');
        }
        
        // Truncate long descriptions
        if (header.includes('description') && value.length > 50) {
            return `<span title="${value}">${value.substring(0, 47)}...</span>`;
        }
        
        return value;
    }

    async populatePreviewFileDropdown() {
        const fileSelect = document.getElementById('preview-file-select');
        if (!fileSelect) return;
        
        try {
            // Get uploaded files
            const uploadedResponse = await fetch(`/api/files/list/${this.config.source}`);
            const uploadedData = uploadedResponse.ok ? await uploadedResponse.json() : { files: [] };
            
            // Get processed files
            const processedResponse = await fetch(`/api/files/${this.config.source}`);
            const processedData = processedResponse.ok ? await processedResponse.json() : { files: [] };
            
            // Clear existing options
            fileSelect.innerHTML = '<option value="">Choose a file...</option>';
            
            // Add uploaded files
            if (uploadedData.files && uploadedData.files.length > 0) {
                const uploadedGroup = document.createElement('optgroup');
                uploadedGroup.label = 'Uploaded Files';
                uploadedData.files.forEach(file => {
                    const option = document.createElement('option');
                    option.value = `uploaded:${file.name}`;
                    option.textContent = `📁 ${file.name}`;
                    uploadedGroup.appendChild(option);
                });
                fileSelect.appendChild(uploadedGroup);
            }
            
            // Add processed files
            if (processedData.files && processedData.files.length > 0) {
                const processedGroup = document.createElement('optgroup');
                processedGroup.label = 'Processed Files';
                processedData.files.forEach(file => {
                    const option = document.createElement('option');
                    option.value = `processed:${file.path}`;
                    option.textContent = `📊 ${file.name} (${file.year}/${this.getMonthName(file.month)})`;
                    processedGroup.appendChild(option);
                });
                fileSelect.appendChild(processedGroup);
            }
            
        } catch (error) {
            console.error('Error populating preview file dropdown:', error);
        }
    }

    async loadFullPreview(fileValue) {
        if (!fileValue) return;
        
        const [fileType, filePath] = fileValue.split(':', 2);
        
        // Show loading state
        this.showPreviewLoading(true);
        
        try {
            let response;
            if (fileType === 'uploaded') {
                response = await fetch(`/api/files/preview-uploaded-full/${this.config.source}?file=${encodeURIComponent(filePath)}`);
            } else if (fileType === 'processed') {
                response = await fetch(`/api/files/preview-full/${this.config.source}?file=${encodeURIComponent(filePath)}`);
            } else {
                throw new Error('Invalid file type');
            }
            
            if (response.ok) {
                const data = await response.json();
                this.displayFullPreview(data, fileType, filePath);
            } else {
                throw new Error('Failed to load file preview');
            }
        } catch (error) {
            this.showAlert('Failed to load file preview: ' + error.message, 'danger');
            this.showPreviewLoading(false);
        }
    }

    displayFullPreview(data, fileType, filePath) {
        // Hide loading state
        this.showPreviewLoading(false);
        
        // Show file info
        this.showPreviewFileInfo(data, fileType);
        
        // Setup sort controls with column options
        this.setupPreviewSortOptions(data.headers);
        
        // Display the full table
        this.displayPreviewTable(data);
        
        // Store current file info for download and sorting
        this.currentPreviewFile = { type: fileType, path: filePath, data: data };
        this.currentPreviewData = data;
    }

    showPreviewFileInfo(data, fileType) {
        const fileInfo = document.getElementById('preview-file-info');
        const filename = document.getElementById('preview-filename');
        const totalRows = document.getElementById('preview-total-rows');
        const fileSize = document.getElementById('preview-file-size');
        const fileTypeSpan = document.getElementById('preview-file-type');
        
        if (fileInfo && filename && totalRows && fileSize && fileTypeSpan) {
            filename.textContent = data.fileName || data.filePath?.split('/').pop() || 'Unknown';
            totalRows.textContent = data.totalRows ? data.totalRows.toLocaleString() : 'Unknown';
            fileSize.textContent = this.formatFileSize(data.fileSize || 0);
            fileTypeSpan.textContent = fileType === 'uploaded' ? 'Uploaded CSV' : 'Processed CSV';
            
            fileInfo.style.display = 'block';
        }
    }

    displayPreviewTable(data) {
        this.displayPreviewTableWithData(data.headers, data.rows);
    }

    displayPreviewTableWithData(headers, rows) {
        const container = document.getElementById('preview-table-container');
        const headersElement = document.getElementById('preview-table-headers');
        const tbody = document.getElementById('preview-table-body');
        const emptyState = document.getElementById('preview-empty-state');
        
        if (!container || !headersElement || !tbody) return;
        
        // Hide empty state
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        // Set up headers
        if (headers && headers.length > 0) {
            headersElement.innerHTML = headers.map(header => `<th>${header}</th>`).join('');
        }
        
        // Set up data - show all rows for full preview
        if (rows && rows.length > 0) {
            tbody.innerHTML = rows.map(row => 
                `<tr>${row.map((cell, index) => {
                    const formattedCell = this.formatTableCell(cell, index, headers);
                    return `<td>${formattedCell}</td>`;
                }).join('')}</tr>`
            ).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="100%" class="text-center text-muted">No data available</td></tr>';
        }
        
        // Show the table container
        container.style.display = 'block';
    }

    showPreviewLoading(show) {
        const loading = document.getElementById('preview-loading');
        const container = document.getElementById('preview-table-container');
        const emptyState = document.getElementById('preview-empty-state');
        
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
        
        if (container) {
            container.style.display = show ? 'none' : 'block';
        }
        
        if (emptyState) {
            emptyState.style.display = show ? 'none' : 'block';
        }
    }

    setupPreviewSortOptions(headers) {
        const sortControls = document.getElementById('preview-sort-controls');
        
        if (sortControls && headers && headers.length > 0) {
            // Populate all three sort dropdowns
            for (let level = 1; level <= 3; level++) {
                const sortColumn = document.getElementById(`preview-sort-column-${level}`);
                
                if (sortColumn) {
                    // Clear existing options
                    sortColumn.innerHTML = '<option value="">No sorting</option>';
                    
                    // Add column options
                    headers.forEach((header, index) => {
                        const option = document.createElement('option');
                        option.value = index;
                        option.textContent = header;
                        sortColumn.appendChild(option);
                    });
                    
                    // Reset sort direction buttons for this level
                    this.updateSortDirectionButtons(level);
                }
            }
            
            // Show sort controls
            sortControls.style.display = 'block';
        }
    }

    clearPreview() {
        // Hide file info
        const fileInfo = document.getElementById('preview-file-info');
        if (fileInfo) {
            fileInfo.style.display = 'none';
        }
        
        // Hide sort controls
        const sortControls = document.getElementById('preview-sort-controls');
        if (sortControls) {
            sortControls.style.display = 'none';
        }
        
        // Hide table container
        const container = document.getElementById('preview-table-container');
        if (container) {
            container.style.display = 'none';
        }
        
        // Show empty state
        const emptyState = document.getElementById('preview-empty-state');
        if (emptyState) {
            emptyState.style.display = 'block';
        }
        
        // Clear current preview file and data
        this.currentPreviewFile = null;
        this.currentPreviewData = null;
    }

    async downloadCurrentPreviewFile() {
        if (!this.currentPreviewFile) {
            this.showAlert('No file selected for download', 'warning');
            return;
        }
        
        try {
            const { type, path } = this.currentPreviewFile;
            let response;
            
            if (type === 'uploaded') {
                // For uploaded files, we need to construct the download path
                response = await fetch(`/api/files/download-uploaded/${this.config.source}?file=${encodeURIComponent(path)}`);
            } else if (type === 'processed') {
                response = await fetch(`/api/files/download/${this.config.source}?file=${encodeURIComponent(path)}`);
            }
            
            if (response && response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = path.split('/').pop();
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showAlert('File downloaded successfully', 'success');
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            this.showAlert('Download failed: ' + error.message, 'danger');
        }
    }

    async checkFiles() {
        try {
            this.showAlert('Checking files...', 'info');
            
            const response = await fetch(`/api/files/validate/${this.config.source}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const result = await response.json();
                this.displayValidationResults(result);
            } else {
                throw new Error('File validation failed');
            }
        } catch (error) {
            this.showAlert('File validation failed: ' + error.message, 'danger');
        }
    }

    async applyFixes(filename) {
        try {
            this.showAlert('Applying automatic fixes...', 'info');
            
            const response = await fetch(`/api/files/fix/${this.config.source}/${encodeURIComponent(filename)}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showAlert('Automatic fixes applied successfully!', 'success');
                
                // Reload the file list to show updated status
                this.loadUploadedFiles();
                
                // Close the validation modal
                this.closeValidationModal();
            } else {
                throw new Error('Failed to apply fixes');
            }
        } catch (error) {
            this.showAlert('Failed to apply fixes: ' + error.message, 'danger');
        }
    }

    closeValidationModal() {
        // Close any open modals
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }

    displayValidationResults(result) {
        const container = document.getElementById('validation-results');
        const content = document.getElementById('validation-results-content');
        
        if (!container || !content) return;
        
        // Debug: Log the validation results to see what's available
        console.log('Validation results:', result);
        if (result.results && result.results.length > 0) {
            console.log('First file validation:', result.results[0].validation);
            console.log('Issues detected:', result.results[0].validation.issues_detected);
        }
        
        container.style.display = 'block';
        
        let html = `
            <div class="mb-3">
                <h6>Validation Summary</h6>
                <p class="mb-2">Checked ${result.files_validated} files for ${this.config.sourceName} format.</p>
            </div>
        `;
        
        if (result.results && result.results.length > 0) {
            result.results.forEach(fileResult => {
                const validation = fileResult.validation;
                const isValid = validation.valid;
                const statusClass = isValid ? 'success' : 'danger';
                const statusIcon = isValid ? 'check-circle' : 'exclamation-triangle';
                
                html += `
                    <div class="card mb-3 border-${statusClass}">
                        <div class="card-header bg-${statusClass} text-white">
                            <div class="d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">
                                    <i class="bi bi-${statusIcon} me-2"></i>
                                    ${fileResult.filename}
                                </h6>
                                <span class="badge bg-light text-dark">
                                    ${fileResult.size_mb.toFixed(2)} MB
                                </span>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <strong>Status:</strong> 
                                    <span class="badge bg-${statusClass}">${isValid ? 'Valid' : 'Invalid'}</span>
                                </div>
                                <div class="col-md-6">
                                    <strong>Records:</strong> ${validation.record_count || 0}
                                </div>
                            </div>
                `;
                
                if (validation.errors && validation.errors.length > 0) {
                    html += `
                        <div class="mt-3">
                            <strong class="text-danger">Errors:</strong>
                            <ul class="list-unstyled mb-0">
                                ${validation.errors.map(error => `<li class="text-danger"><i class="bi bi-x-circle me-1"></i>${error}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                if (validation.warnings && validation.warnings.length > 0) {
                    html += `
                        <div class="mt-3">
                            <strong class="text-warning">Warnings:</strong>
                            <ul class="list-unstyled mb-0">
                                ${validation.warnings.map(warning => `<li class="text-warning"><i class="bi bi-exclamation-triangle me-1"></i>${warning}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                if (validation.info) {
                    html += `
                        <div class="mt-3">
                            <strong class="text-info">Info:</strong>
                            <p class="mb-0 text-info">${validation.info}</p>
                        </div>
                    `;
                }
                
                // Simple fix detection and user permission
                if (validation.issues_detected && Array.isArray(validation.issues_detected) && validation.issues_detected.length > 0) {
                    const fixableIssues = validation.issues_detected.filter(issue => issue.fixable);
                    const unfixableIssues = validation.issues_detected.filter(issue => !issue.fixable);
                    
                    if (fixableIssues.length > 0) {
                        html += `
                            <div class="mt-3">
                                <div class="alert alert-success border-0">
                                    <div class="d-flex align-items-center mb-2">
                                        <i class="bi bi-check-circle me-2"></i>
                                        <strong>Automatic Fix Available</strong>
                                    </div>
                                    <p class="mb-2">The following issues can be fixed automatically:</p>
                                    <ul class="mb-3">
                                        ${fixableIssues.map(issue => `
                                            <li>${issue.message || issue}
                                                ${issue.suggestion ? `<br><small class="text-muted">💡 ${issue.suggestion}</small>` : ''}
                                            </li>
                                        `).join('')}
                                    </ul>
                                    <div class="d-flex gap-2">
                                        <button type="button" class="btn btn-success btn-sm" onclick="sourceApp.applyFixes('${fileResult.filename}')">
                                            <i class="bi bi-wrench me-1"></i>
                                            Yes, Apply Fixes
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="sourceApp.closeValidationModal()">
                                            No, Keep As-Is
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    if (unfixableIssues.length > 0) {
                        html += `
                            <div class="mt-3">
                                <div class="alert alert-warning border-0">
                                    <div class="d-flex align-items-center mb-2">
                                        <i class="bi bi-exclamation-triangle me-2"></i>
                                        <strong>Manual Fix Required</strong>
                                    </div>
                                    <ul class="mb-0">
                                        ${unfixableIssues.map(issue => `
                                            <li>${issue.message || issue}
                                                ${issue.suggestion ? `<br><small class="text-muted">💡 ${issue.suggestion}</small>` : ''}
                                            </li>
                                        `).join('')}
                                    </ul>
                                </div>
                            </div>
                        `;
                    }
                }
                
                html += `
                        </div>
                    </div>
                `;
            });
        } else {
            html += `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No files found to validate.
                </div>
            `;
        }
        
        content.innerHTML = html;
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('fileAnalysisModal'));
        modal.show();
        
        // Scroll to validation results
        container.scrollIntoView({ behavior: 'smooth' });
    }

    async analyzeFile(filePath) {
        console.log('analyzeFile called with filePath:', filePath);
        
        // Navigate to analytics page with file parameters
        const analyticsUrl = `/source/${this.config.source}/analytics?fileType=processed&filePath=${encodeURIComponent(filePath)}`;
        window.location.href = analyticsUrl;
    }

    async analyzeUploadedFile(filename) {
        console.log('analyzeUploadedFile called with filename:', filename);
        
        // Navigate to analytics page with file parameters
        const analyticsUrl = `/source/${this.config.source}/analytics?fileType=uploaded&filePath=${encodeURIComponent(filename)}`;
        window.location.href = analyticsUrl;
    }

    displayFileAnalysis(result) {
        const analysis = result.analysis;
        
        // Debug: Log the validation result to see what's available
        console.log('Validation result:', analysis.validation);
        console.log('Issues detected:', analysis.validation.issues_detected);
        console.log('Errors:', analysis.validation.errors);
        console.log('Warnings:', analysis.validation.warnings);
        console.log('Fixable issues:', analysis.validation.issues_detected ? analysis.validation.issues_detected.filter(issue => issue.fixable) : 'No issues detected');
        console.log('Unfixable issues:', analysis.validation.issues_detected ? analysis.validation.issues_detected.filter(issue => !issue.fixable) : 'No issues detected');
        
        // Convert file size from bytes to MB
        const fileSizeMB = (analysis.file_size_bytes / (1024 * 1024)).toFixed(2);
        
        let html = `
            <div class="modal fade" id="fileAnalysisModal" tabindex="-1" aria-modal="true" role="dialog" style="z-index: 1060;">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content border-0 shadow-lg" style="background-color: white;">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-file-earmark-text me-2"></i>
                                File Validation: ${result.filename}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-4" style="background-color: white;">
                            <!-- File Overview -->
                            <div class="row mb-4">
                                <div class="col-md-3">
                                    <div class="card border-0 bg-light">
                                        <div class="card-body text-center">
                                            <i class="bi bi-file-earmark-text fs-1 text-primary mb-2"></i>
                                            <h6 class="card-title">File Size</h6>
                                            <p class="card-text fw-bold">${fileSizeMB} MB</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card border-0 bg-light">
                                        <div class="card-body text-center">
                                            <i class="bi bi-list-ul fs-1 text-info mb-2"></i>
                                            <h6 class="card-title">Columns</h6>
                                            <p class="card-text fw-bold">${analysis.columns.length}</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card border-0 bg-light">
                                        <div class="card-body text-center">
                                            <i class="bi bi-gear fs-1 text-warning mb-2"></i>
                                            <h6 class="card-title">Source</h6>
                                            <p class="card-text fw-bold">${result.source}</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card border-0 bg-light">
                                        <div class="card-body text-center">
                                            <i class="bi bi-check-circle fs-1 ${analysis.validation.is_valid ? 'text-success' : 'text-danger'} mb-2"></i>
                                            <h6 class="card-title">Validation</h6>
                                            <p class="card-text fw-bold">${analysis.validation.is_valid ? 'Valid' : 'Invalid'}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Validation Results -->
                            <div class="mb-4">
                                <h6 class="text-muted mb-3">
                                    <i class="bi bi-list-check me-2"></i>
                                    Column Validation
                                </h6>
                                
                                <!-- Required Columns -->
                                <div class="mb-3">
                                    <h6 class="text-success mb-2">
                                        <i class="bi bi-check-circle me-2"></i>
                                        Required Columns (${analysis.validation.present_columns.length}/${analysis.validation.required_columns.length})
                                    </h6>
                                    <div class="d-flex flex-wrap gap-2">
                                        ${analysis.validation.required_columns.map(col => {
                                            const isPresent = analysis.validation.present_columns.includes(col);
                                            return `<span class="badge ${isPresent ? 'bg-success' : 'bg-danger'} rounded-pill">${col}</span>`;
                                        }).join('')}
                                    </div>
                                </div>
                                
                                <!-- Missing Columns Warning -->
                                ${analysis.validation.missing_columns.length > 0 ? `
                                    <div class="alert alert-danger border-0 shadow-sm">
                                        <div class="d-flex align-items-center mb-2">
                                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                            <h6 class="mb-0">Missing Required Columns (${analysis.validation.missing_columns.length})</h6>
                                        </div>
                                        <ul class="mb-0 ps-3">
                                            ${analysis.validation.missing_columns.map(col => `<li class="mb-1">${col}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : `
                                    <div class="alert alert-success border-0 shadow-sm">
                                        <div class="d-flex align-items-center">
                                            <i class="bi bi-check-circle-fill me-2"></i>
                                            <span class="mb-0">All required columns are present!</span>
                                        </div>
                                    </div>
                                `}
                                
                                <!-- Enhanced Validation Information -->
                                ${analysis.validation.fixes_applied && Array.isArray(analysis.validation.fixes_applied) && analysis.validation.fixes_applied.length > 0 ? `
                                    <div class="alert alert-success border-0 shadow-sm mt-3">
                                        <div class="d-flex align-items-center mb-2">
                                            <i class="bi bi-check-circle-fill me-2"></i>
                                            <h6 class="mb-0">Automatic Fixes Applied</h6>
                                        </div>
                                        <ul class="mb-0 ps-3">
                                            ${analysis.validation.fixes_applied.map(fix => `<li class="mb-1">${fix}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                                
                                ${analysis.validation.issues_detected && Array.isArray(analysis.validation.issues_detected) && analysis.validation.issues_detected.length > 0 ? `
                                    <div class="alert alert-warning border-0 shadow-sm mt-3">
                                        <div class="d-flex align-items-center mb-2">
                                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                            <h6 class="mb-0">Issues Detected</h6>
                                        </div>
                                        <ul class="mb-0 ps-3">
                                            ${analysis.validation.issues_detected.map(issue => `
                                                <li class="mb-1">
                                                    ${issue.message || issue}
                                                    ${issue.fixable ? ' <span class="badge bg-success">Fixable</span>' : ' <span class="badge bg-danger">Manual Fix Required</span>'}
                                                </li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                    
                                    <!-- Fix Permission Prompt -->
                                    ${(() => {
                                        console.log('Building fix permission prompt...');
                                        const fixableIssues = analysis.validation.issues_detected.filter(issue => issue.fixable);
                                        const unfixableIssues = analysis.validation.issues_detected.filter(issue => !issue.fixable);
                                        
                                        console.log('Fixable issues:', fixableIssues.length);
                                        console.log('Unfixable issues:', unfixableIssues.length);
                                        
                                        let promptHtml = '';
                                        
                                        if (fixableIssues.length > 0) {
                                            promptHtml += `
                                                <div class="alert alert-success border-0 shadow-sm mt-3">
                                                    <div class="d-flex align-items-center mb-2">
                                                        <i class="bi bi-check-circle me-2"></i>
                                                        <strong>Automatic Fix Available</strong>
                                                    </div>
                                                    <p class="mb-2">The following issues can be fixed automatically:</p>
                                                    <ul class="mb-3">
                                                        ${fixableIssues.map(issue => `
                                                            <li>${issue.message || issue}
                                                                ${issue.suggestion ? `<br><small class="text-muted">💡 ${issue.suggestion}</small>` : ''}
                                                            </li>
                                                        `).join('')}
                                                    </ul>
                                                    <div class="d-flex gap-2">
                                                        <button type="button" class="btn btn-success btn-sm" onclick="sourceApp.applyFixes('${result.filename}')">
                                                            <i class="bi bi-wrench me-1"></i>
                                                            Yes, Apply Fixes
                                                        </button>
                                                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="sourceApp.closeValidationModal()">
                                                            No, Keep As-Is
                                                        </button>
                                                    </div>
                                                </div>
                                            `;
                                        }
                                        
                                        if (unfixableIssues.length > 0) {
                                            promptHtml += `
                                                <div class="alert alert-warning border-0 shadow-sm mt-3">
                                                    <div class="d-flex align-items-center mb-2">
                                                        <i class="bi bi-exclamation-triangle me-2"></i>
                                                        <strong>Manual Fix Required</strong>
                                                    </div>
                                                    <ul class="mb-0">
                                                        ${unfixableIssues.map(issue => `
                                                            <li>${issue.message || issue}
                                                                ${issue.suggestion ? `<br><small class="text-muted">💡 ${issue.suggestion}</small>` : ''}
                                                            </li>
                                                        `).join('')}
                                                    </ul>
                                                </div>
                                            `;
                                        }
                                        
                                        return promptHtml;
                                    })()}
                                ` : ''}
                                
                                ${analysis.validation.fix_suggestions && Array.isArray(analysis.validation.fix_suggestions) && analysis.validation.fix_suggestions.length > 0 ? `
                                    <div class="alert alert-info border-0 shadow-sm mt-3">
                                        <div class="d-flex align-items-center mb-2">
                                            <i class="bi bi-lightbulb-fill me-2"></i>
                                            <h6 class="mb-0">Fix Suggestions</h6>
                                        </div>
                                        <ul class="mb-0 ps-3">
                                            ${analysis.validation.fix_suggestions.map(suggestion => `<li class="mb-1">${suggestion}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                                
                                ${analysis.validation.user_action_required ? `
                                    <div class="alert alert-warning border-0 shadow-sm mt-3">
                                        <div class="d-flex align-items-center">
                                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                            <strong>User Action Required</strong>
                                        </div>
                                        <p class="mb-0 mt-2">This file has issues that require manual intervention before processing can proceed.</p>
                                    </div>
                                ` : ''}
                                
                                ${analysis.validation.can_proceed === false ? `
                                    <div class="alert alert-danger border-0 shadow-sm mt-3">
                                        <div class="d-flex align-items-center">
                                            <i class="bi bi-x-circle-fill me-2"></i>
                                            <strong>Processing Blocked</strong>
                                        </div>
                                        <p class="mb-0 mt-2">This file cannot be processed until the issues are resolved.</p>
                                    </div>
                                ` : ''}
                            </div>
                            
                            <!-- All Columns Found -->
                            <div class="mb-4">
                                <h6 class="text-muted mb-3">
                                    <i class="bi bi-list-ul me-2"></i>
                                    All Columns Found
                                </h6>
                                <div class="d-flex flex-wrap gap-2">
                                    ${analysis.columns.map(col => `<span class="badge bg-primary rounded-pill">${col}</span>`).join('')}
                                </div>
                            </div>
        `;
        
        if (analysis.sample_data && analysis.sample_data.length > 0) {
            html += `
                <div class="mb-4">
                    <h6 class="text-muted mb-3">
                        <i class="bi bi-table me-2"></i>
                        Sample Data (First 5 Rows)
                    </h6>
                    <div class="card border-0 shadow-sm">
                        <div class="card-body p-0">
                            <div class="table-responsive" style="max-height: 300px;">
                                <table class="table table-sm table-hover mb-0">
                                    <thead class="table-light sticky-top">
                                        <tr>
                                            ${Object.keys(analysis.sample_data[0] || {}).map(key => `<th class="border-0">${key}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${analysis.sample_data.map(row => 
                                            `<tr>${Object.values(row).map(val => `<td class="border-0">${val || ''}</td>`).join('')}</tr>`
                                        ).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += `
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
        `;
        
        // Remove existing modal and overlays
        const existingModal = document.getElementById('fileAnalysisModal');
        if (existingModal) {
            if (bootstrap.Modal.getInstance(existingModal)) {
                bootstrap.Modal.getInstance(existingModal).dispose();
            }
            existingModal.remove();
        }
        
        // Remove all modal backdrops and clean up body
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // Temporarily disable drag & drop events
        const uploadZone = document.getElementById('upload-zone');
        if (uploadZone) {
            uploadZone.style.pointerEvents = 'none';
        }
        
        // Add new modal to body with high z-index
        document.body.insertAdjacentHTML('beforeend', html);
        
        // Force reflow and ensure modal is visible
        const modalEl = document.getElementById('fileAnalysisModal');
        void modalEl.offsetWidth;
        
        // Initialize and show modal with static backdrop (no see-through)
        const modal = new bootstrap.Modal(modalEl, { 
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
                backdrop.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                backdrop.style.opacity = '1';
            }
        }, 10);
        
        // Re-enable drag & drop after modal is shown
        setTimeout(() => {
            if (uploadZone) {
                uploadZone.style.pointerEvents = '';
            }
        }, 500);
    }
}

// Initialize the source application
let sourceApp;
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - initializing SourceApp');
    sourceApp = new SourceApp();
}); 