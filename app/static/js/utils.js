/**
 * Garlic and Chives - Utility Functions
 * Common utility functions used throughout the application
 */

class Utils {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Global event listeners
        document.addEventListener('keydown', (e) => {
            // Escape key closes modals
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    // Date and Time Utilities
    formatDate(date, format = 'MM/DD/YYYY') {
        if (!date) return '';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';

        const pad = (num) => String(num).padStart(2, '0');
        
        const formats = {
            'MM/DD/YYYY': `${pad(d.getMonth() + 1)}/${pad(d.getDate())}/${d.getFullYear()}`,
            'YYYY-MM-DD': `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
            'MM/DD/YY': `${pad(d.getMonth() + 1)}/${pad(d.getDate())}/${String(d.getFullYear()).slice(-2)}`,
            'MMM DD, YYYY': d.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                year: 'numeric' 
            }),
            'DD MMM YYYY': d.toLocaleDateString('en-US', { 
                day: 'numeric', 
                month: 'short', 
                year: 'numeric' 
            })
        };

        return formats[format] || formats['MM/DD/YYYY'];
    }

    formatDateTime(date, format = 'MM/DD/YYYY HH:mm') {
        if (!date) return '';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';

        const dateStr = this.formatDate(d, 'MM/DD/YYYY');
        const timeStr = d.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        return `${dateStr} ${timeStr}`;
    }

    parseDate(dateString, format = 'MM/DD/YYYY') {
        if (!dateString) return null;

        // Handle different date formats
        const patterns = {
            'MM/DD/YYYY': /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/,
            'YYYY-MM-DD': /^(\d{4})-(\d{1,2})-(\d{1,2})$/,
            'MM/DD/YY': /^(\d{1,2})\/(\d{1,2})\/(\d{2})$/
        };

        const pattern = patterns[format];
        if (!pattern) return new Date(dateString);

        const match = dateString.match(pattern);
        if (!match) return null;

        if (format === 'MM/DD/YY') {
            const year = parseInt(match[3]) + 2000;
            return new Date(year, parseInt(match[1]) - 1, parseInt(match[2]));
        } else {
            return new Date(parseInt(match[3]), parseInt(match[1]) - 1, parseInt(match[2]));
        }
    }

    getRelativeTime(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
        if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        return 'Just now';
    }

    // Number and Currency Utilities
    formatCurrency(amount, currency = 'USD', locale = 'en-US') {
        if (amount === null || amount === undefined) return '';
        
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    formatNumber(number, decimals = 2, locale = 'en-US') {
        if (number === null || number === undefined) return '';
        
        return new Intl.NumberFormat(locale, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatPercentage(value, total, decimals = 1) {
        if (total === 0) return '0%';
        return `${((value / total) * 100).toFixed(decimals)}%`;
    }

    // String Utilities
    truncateString(str, maxLength = 50, suffix = '...') {
        if (!str || str.length <= maxLength) return str;
        return str.substring(0, maxLength - suffix.length) + suffix;
    }

    capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }

    toTitleCase(str) {
        if (!str) return '';
        return str.replace(/\w\S*/g, (txt) => 
            txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
        );
    }

    slugify(str) {
        if (!str) return '';
        return str
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    // Array and Object Utilities
    groupBy(array, key) {
        return array.reduce((groups, item) => {
            const group = item[key];
            groups[group] = groups[group] || [];
            groups[group].push(item);
            return groups;
        }, {});
    }

    sortBy(array, key, direction = 'asc') {
        return [...array].sort((a, b) => {
            let aVal = a[key];
            let bVal = b[key];

            // Handle nested properties
            if (key.includes('.')) {
                const keys = key.split('.');
                aVal = keys.reduce((obj, k) => obj?.[k], a);
                bVal = keys.reduce((obj, k) => obj?.[k], b);
            }

            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }

            if (direction === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }

    unique(array, key = null) {
        if (key) {
            const seen = new Set();
            return array.filter(item => {
                const value = item[key];
                if (seen.has(value)) {
                    return false;
                }
                seen.add(value);
                return true;
            });
        }
        return [...new Set(array)];
    }

    // DOM Utilities
    createElement(tag, className = '', innerHTML = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    }

    addClass(element, className) {
        if (element && element.classList) {
            element.classList.add(className);
        }
    }

    removeClass(element, className) {
        if (element && element.classList) {
            element.classList.remove(className);
        }
    }

    toggleClass(element, className) {
        if (element && element.classList) {
            element.classList.toggle(className);
        }
    }

    hasClass(element, className) {
        return element && element.classList && element.classList.contains(className);
    }

    // Event Utilities
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Storage Utilities
    setLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    }

    getLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    }

    removeLocalStorage(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Error removing from localStorage:', error);
        }
    }

    clearLocalStorage() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Error clearing localStorage:', error);
        }
    }

    // Validation Utilities
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    isValidDate(date) {
        const d = new Date(date);
        return d instanceof Date && !isNaN(d);
    }

    isNumeric(value) {
        return !isNaN(parseFloat(value)) && isFinite(value);
    }

    // File Utilities
    getFileExtension(filename) {
        return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
    }

    isValidFileType(filename, allowedTypes) {
        const extension = this.getFileExtension(filename).toLowerCase();
        return allowedTypes.includes(`.${extension}`);
    }

    // Color Utilities
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }

    // Modal Utilities
    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            if (window.components && window.components.closeModal) {
                const modalId = modal.id;
                if (modalId) {
                    window.components.closeModal(modalId);
                }
            }
        });
    }

    // Loading Utilities
    showLoading(message = 'Loading...') {
        if (window.components && window.components.showLoading) {
            window.components.showLoading(message);
        }
    }

    hideLoading() {
        if (window.components && window.components.hideLoading) {
            window.components.hideLoading();
        }
    }

    // Notification Utilities
    showNotification(message, type = 'info', duration = 5000) {
        if (window.components && window.components.showNotification) {
            window.components.showNotification(message, type, duration);
        }
    }

    // Error Handling
    handleError(error, context = '') {
        console.error(`Error in ${context}:`, error);
        
        let message = 'An error occurred';
        if (error.message) {
            message = error.message;
        }

        this.showNotification(message, 'error');
        
        return {
            success: false,
            error: message,
            context
        };
    }

    // Async Utilities
    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async retry(fn, maxAttempts = 3, delay = 1000) {
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await fn();
            } catch (error) {
                if (attempt === maxAttempts) {
                    throw error;
                }
                await this.sleep(delay * attempt);
            }
        }
    }

    // CSV Utilities
    parseCSV(csv, delimiter = ',') {
        const lines = csv.split('\n');
        const headers = lines[0].split(delimiter).map(h => h.trim().replace(/"/g, ''));
        const data = [];

        for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim()) {
                const values = lines[i].split(delimiter).map(v => v.trim().replace(/"/g, ''));
                const row = {};
                headers.forEach((header, index) => {
                    row[header] = values[index] || '';
                });
                data.push(row);
            }
        }

        return data;
    }

    // Export utilities
    exportToCSV(data, filename = 'export.csv') {
        if (!data || data.length === 0) return;

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Initialize utilities when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.utils = new Utils();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
} 