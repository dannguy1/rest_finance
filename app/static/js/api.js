/**
 * Garlic and Chives - API Client
 * Handles all API communication with the backend
 */

class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
        this.endpoints = {
            health: '/api/health',
            files: '/api/files',
            processing: '/api/processing',
            upload: '/api/upload'
        };
        this.setupInterceptors();
    }

    setupInterceptors() {
        // Add request/response interceptors if needed
        this.requestInterceptor = (config) => {
            // Add auth headers, etc.
            return config;
        };

        this.responseInterceptor = (response) => {
            // Handle common response patterns
            return response;
        };
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            // Apply request interceptor
            const interceptedConfig = this.requestInterceptor(config);
            
            const response = await fetch(url, interceptedConfig);
            
            // Apply response interceptor
            const interceptedResponse = this.responseInterceptor(response);

            if (!interceptedResponse.ok) {
                throw new Error(`HTTP error! status: ${interceptedResponse.status}`);
            }

            const contentType = interceptedResponse.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await interceptedResponse.json();
            } else {
                return await interceptedResponse.text();
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Health Check Endpoints
    async getHealth() {
        return this.request(this.endpoints.health);
    }

    async getDetailedHealth() {
        return this.request(`${this.endpoints.health}/detailed`);
    }

    async getReadiness() {
        return this.request(`${this.endpoints.health}/ready`);
    }

    async getLiveness() {
        return this.request(`${this.endpoints.health}/live`);
    }

    async getMetrics() {
        return this.request(`${this.endpoints.health}/metrics`);
    }

    // File Management Endpoints
    async uploadFile(source, file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        if (options.processingOptions) {
            formData.append('processing_options', JSON.stringify(options.processingOptions));
        }

        return this.request(`${this.endpoints.files}/upload/${source}`, {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    }

    async listFiles(source) {
        return this.request(`${this.endpoints.files}/list/${source}`);
    }

    async deleteFile(source, filename) {
        return this.request(`${this.endpoints.files}/${source}/${filename}`, {
            method: 'DELETE'
        });
    }

    async validateFile(source, filename) {
        return this.request(`${this.endpoints.files}/validate/${source}/${filename}`);
    }

    async getFileInfo(source, filename) {
        return this.request(`${this.endpoints.files}/info/${source}/${filename}`);
    }

    async backupFile(source, filename) {
        return this.request(`${this.endpoints.files}/backup/${source}/${filename}`, {
            method: 'POST'
        });
    }

    async listOutputFiles(source, year = null) {
        const params = year ? `?year=${year}` : '';
        return this.request(`${this.endpoints.files}/output/${source}${params}`);
    }

    async downloadOutputFile(source, year, month) {
        return this.request(`${this.endpoints.files}/download/${source}/${year}/${month}`, {
            method: 'GET'
        });
    }

    async cleanupOldFiles(daysOld = 30) {
        return this.request(`${this.endpoints.files}/cleanup`, {
            method: 'POST',
            body: JSON.stringify({ days_old: daysOld })
        });
    }

    // Processing Endpoints
    async processData(source, year, options = {}) {
        return this.request(`${this.endpoints.processing}/process/${source}/${year}`, {
            method: 'POST',
            body: JSON.stringify(options)
        });
    }

    async getProcessingStatus(source, year) {
        return this.request(`${this.endpoints.processing}/status/${source}/${year}`);
    }

    async getProcessingSummary(source, year) {
        return this.request(`${this.endpoints.processing}/summary/${source}/${year}`);
    }

    async downloadProcessedFile(source, year, month) {
        return this.request(`${this.endpoints.processing}/download/${source}/${year}/${month}`, {
            method: 'GET'
        });
    }

    async getAvailableSources() {
        return this.request(`${this.endpoints.processing}/sources`);
    }

    async getAvailableYears(source) {
        return this.request(`${this.endpoints.processing}/years/${source}`);
    }

    async getAvailableMonths(source, year) {
        return this.request(`${this.endpoints.processing}/months/${source}/${year}`);
    }

    // WebSocket Connection for Real-time Updates
    connectWebSocket(source, year, onMessage, onError) {
        const wsUrl = `ws://${window.location.host}/api/processing/ws/${source}/${year}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket connected');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (onMessage) onMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (onError) onError(error);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
        };

        return ws;
    }

    // Batch Operations
    async uploadMultipleFiles(source, files, options = {}) {
        const promises = files.map(file => this.uploadFile(source, file, options));
        return Promise.allSettled(promises);
    }

    async processMultipleSources(sources, year, options = {}) {
        const promises = sources.map(source => this.processData(source, year, options));
        return Promise.allSettled(promises);
    }

    // Error Handling
    handleError(error, context = '') {
        console.error(`API Error in ${context}:`, error);
        
        let message = 'An error occurred';
        if (error.message) {
            message = error.message;
        } else if (error.detail) {
            message = error.detail;
        }

        // Show notification
        if (window.components) {
            window.components.showNotification(message, 'error');
        }

        return {
            success: false,
            error: message,
            context
        };
    }

    // Response Validation
    validateResponse(response, expectedFields = []) {
        if (!response) {
            throw new Error('No response received');
        }

        for (const field of expectedFields) {
            if (!(field in response)) {
                throw new Error(`Missing required field: ${field}`);
            }
        }

        return response;
    }

    // Progress Tracking
    async trackProgress(jobId, onProgress, onComplete, onError) {
        const maxAttempts = 60; // 5 minutes with 5-second intervals
        let attempts = 0;

        const checkProgress = async () => {
            try {
                const response = await this.getProcessingStatus(jobId);
                
                if (onProgress) {
                    onProgress(response);
                }

                if (response.status === 'completed') {
                    if (onComplete) onComplete(response);
                    return;
                }

                if (response.status === 'error') {
                    if (onError) onError(response);
                    return;
                }

                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkProgress, 5000); // Check every 5 seconds
                } else {
                    if (onError) onError(new Error('Progress tracking timeout'));
                }
            } catch (error) {
                if (onError) onError(error);
            }
        };

        checkProgress();
    }

    // File Download Helpers
    async downloadFileAsBlob(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Download failed: ${response.status}`);
        }
        return response.blob();
    }

    async downloadAndSaveFile(url, filename) {
        try {
            const blob = await this.downloadFileAsBlob(url);
            const downloadUrl = window.URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            window.URL.revokeObjectURL(downloadUrl);
            
            return { success: true, filename };
        } catch (error) {
            return this.handleError(error, 'download');
        }
    }

    // Cache Management
    clearCache() {
        // Clear any cached data
        if (window.caches) {
            caches.keys().then(names => {
                names.forEach(name => {
                    caches.delete(name);
                });
            });
        }
    }

    // Rate Limiting
    setupRateLimiting(maxRequests = 10, timeWindow = 60000) {
        this.rateLimiter = {
            maxRequests,
            timeWindow,
            requests: []
        };
    }

    async rateLimitedRequest(endpoint, options = {}) {
        if (!this.rateLimiter) {
            return this.request(endpoint, options);
        }

        const now = Date.now();
        this.rateLimiter.requests = this.rateLimiter.requests.filter(
            time => now - time < this.rateLimiter.timeWindow
        );

        if (this.rateLimiter.requests.length >= this.rateLimiter.maxRequests) {
            throw new Error('Rate limit exceeded. Please try again later.');
        }

        this.rateLimiter.requests.push(now);
        return this.request(endpoint, options);
    }
}

// Initialize API client when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.api = new APIClient();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
} 