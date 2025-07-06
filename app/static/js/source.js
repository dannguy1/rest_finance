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
        this.loadUploadedFiles();
        this.loadProcessedFiles();
        this.setupPreviewTab();
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
        try {
            const response = await fetch(`/api/files/${this.config.source}`);
            if (response.ok) {
                const data = await response.json();
                this.displayProcessedFiles(data.files);
                this.populateYearFilter(data.years);
            } else {
                throw new Error('Failed to load files');
            }
        } catch (error) {
            this.showAlert('Failed to load processed files', 'danger');
        }
    }

    displayProcessedFiles(files) {
        const tbody = document.getElementById('files-table-body');
        const emptyState = document.getElementById('empty-state');
        
        if (!tbody) return;

        if (files.length === 0) {
            tbody.innerHTML = '';
            if (emptyState) {
                emptyState.style.display = 'block';
            }
            return;
        }

        if (emptyState) {
            emptyState.style.display = 'none';
        }

        tbody.innerHTML = '';
        
        files.forEach(file => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <i class="bi bi-file-earmark-text me-2"></i>
                    ${file.name}
                </td>
                <td>${file.year}</td>
                <td>${this.getMonthName(file.month)}</td>
                <td>${this.formatFileSize(file.size)}</td>
                <td>${this.formatDate(file.modified)}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-primary" title="Preview" onclick="sourceApp.previewFile('${file.path}')">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button type="button" class="btn btn-outline-success" title="Download" onclick="sourceApp.downloadFile('${file.path}')">
                            <i class="bi bi-download"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger" title="Delete" onclick="sourceApp.deleteProcessedFile(${file.year}, ${parseInt(file.month, 10)})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    populateYearFilter(years) {
        const yearFilter = document.getElementById('year-filter');
        if (yearFilter) {
            // Keep the "All Years" option
            yearFilter.innerHTML = '<option value="">All Years</option>';
            
            years.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                yearFilter.appendChild(option);
            });
        }
    }

    filterFiles() {
        const yearFilter = document.getElementById('year-filter');
        const monthFilter = document.getElementById('month-filter');
        
        const year = yearFilter ? yearFilter.value : '';
        const month = monthFilter ? monthFilter.value : '';
        
        // Reload files with filters
        this.loadProcessedFilesWithFilters(year, month);
    }

    async loadProcessedFilesWithFilters(year, month) {
        try {
            const params = new URLSearchParams();
            if (year) params.append('year', year);
            if (month) params.append('month', month);
            
            const response = await fetch(`/api/files/${this.config.source}?${params}`);
            if (response.ok) {
                const data = await response.json();
                this.displayProcessedFiles(data.files);
            }
        } catch (error) {
            this.showAlert('Failed to filter files', 'danger');
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
        
        // Set the file in the preview dropdown and load it
        const previewDropdown = document.getElementById('preview-file-select');
        if (previewDropdown) {
            // Find the option that matches this file path
            for (let option of previewDropdown.options) {
                if (option.value === filePath) {
                    previewDropdown.value = filePath;
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
                    group_by_description: true,
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
                    group_by_description: true,
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
        try {
            const response = await fetch(`/api/files/preview-uploaded/${this.config.source}?file=${encodeURIComponent(filename)}`);
            if (response.ok) {
                const data = await response.json();
                this.showFilePreview(data);
            } else {
                throw new Error('Failed to load file preview');
            }
        } catch (error) {
            this.showAlert('Failed to load file preview: ' + error.message, 'danger');
        }
    }

    setupPreviewTab() {
        // Setup file selection dropdown
        const fileSelect = document.getElementById('preview-file-select');
        const loadBtn = document.getElementById('load-preview-btn');
        
        if (fileSelect && loadBtn) {
            // Auto-load preview when file is selected
            fileSelect.addEventListener('change', () => {
                if (fileSelect.value) {
                    this.loadFullPreview(fileSelect.value);
                } else {
                    // Clear preview when no file is selected
                    this.clearPreview();
                }
                // Keep button state for backward compatibility
                loadBtn.disabled = !fileSelect.value;
            });
            
            // Load preview when button is clicked (for manual trigger)
            loadBtn.addEventListener('click', () => {
                if (fileSelect.value) {
                    this.loadFullPreview(fileSelect.value);
                }
            });
            
            // Load preview when Enter is pressed
            fileSelect.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && fileSelect.value) {
                    this.loadFullPreview(fileSelect.value);
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
        
        // Populate file dropdown
        this.populatePreviewFileDropdown();
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
        
        // Display the full table
        this.displayPreviewTable(data);
        
        // Store current file info for download
        this.currentPreviewFile = { type: fileType, path: filePath, data: data };
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
        const container = document.getElementById('preview-table-container');
        const headers = document.getElementById('preview-table-headers');
        const tbody = document.getElementById('preview-table-body');
        const emptyState = document.getElementById('preview-empty-state');
        
        if (!container || !headers || !tbody) return;
        
        // Hide empty state
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        // Set up headers
        if (data.headers && data.headers.length > 0) {
            headers.innerHTML = data.headers.map(header => `<th>${header}</th>`).join('');
        }
        
        // Set up data - show all rows for full preview
        if (data.rows && data.rows.length > 0) {
            tbody.innerHTML = data.rows.map(row => 
                `<tr>${row.map(cell => `<td>${cell || ''}</td>`).join('')}</tr>`
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

    clearPreview() {
        // Hide file info
        const fileInfo = document.getElementById('preview-file-info');
        if (fileInfo) {
            fileInfo.style.display = 'none';
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
        
        // Clear current preview file
        this.currentPreviewFile = null;
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

    async analyzeFile(filename) {
        try {
            console.log('analyzeFile called with filename:', filename);
            this.showAlert('Analyzing file...', 'info');
            
            const response = await fetch(`/api/files/analyze/${this.config.source}/${encodeURIComponent(filename)}`);
            
            if (response.ok) {
                const result = await response.json();
                console.log('Analysis result received:', result);
                this.displayFileAnalysis(result);
            } else {
                throw new Error('File analysis failed');
            }
        } catch (error) {
            console.error('Error in analyzeFile:', error);
            this.showAlert('File analysis failed: ' + error.message, 'danger');
        }
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
    sourceApp = new SourceApp();
}); 