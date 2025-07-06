class SourceAnalyticsApp {
    constructor() {
        this.config = window.sourceConfig;
        this.currentFile = null;
        this.charts = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkForSelectedFile();
    }

    setupEventListeners() {
        // Tab change events
        const tabs = document.querySelectorAll('#analyticsTabs button[data-bs-toggle="tab"]');
        tabs.forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                if (e.target.id === 'group-by-description-tab') {
                    this.loadGroupByDescription();
                } else if (e.target.id === 'monthly-summary-tab') {
                    this.loadMonthlySummary();
                } else if (e.target.id === 'amount-analysis-tab') {
                    this.loadAmountAnalysis();
                } else if (e.target.id === 'trends-tab') {
                    this.loadTrends();
                }
            });
        });

        // Search functionality
        const searchInput = document.getElementById('description-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterDescriptionTable(e.target.value);
            });
        }

        // Export functionality
        const exportBtn = document.getElementById('export-description-data');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportDescriptionData();
            });
        }
    }

    checkForSelectedFile() {
        // Check if there's a file selected from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const fileType = urlParams.get('fileType');
        const filePath = urlParams.get('filePath');
        
        if (fileType && filePath) {
            this.currentFile = { type: fileType, path: filePath };
            this.showFileInfo();
            this.loadGroupByDescription();
        }
    }

    showFileInfo() {
        if (!this.currentFile) return;

        const fileInfo = document.getElementById('file-selection-info');
        const filename = document.getElementById('analytics-filename');
        const totalRows = document.getElementById('analytics-total-rows');
        const fileType = document.getElementById('analytics-file-type');

        if (fileInfo && filename && totalRows && fileType) {
            filename.textContent = this.currentFile.path.split('/').pop();
            fileType.textContent = this.currentFile.type === 'uploaded' ? 'Uploaded CSV' : 'Processed CSV';
            fileInfo.style.display = 'block';
        }
    }

    async loadGroupByDescription() {
        if (!this.currentFile) {
            this.showEmptyState('group-by-description');
            return;
        }

        this.showLoading('group-by-description');
        
        try {
            const response = await fetch(`/api/files/analytics/${this.config.source}/group-by-description?fileType=${this.currentFile.type}&filePath=${encodeURIComponent(this.currentFile.path)}`);
            
            if (response.ok) {
                const data = await response.json();
                this.displayGroupByDescription(data);
            } else {
                throw new Error('Failed to load group by description data');
            }
        } catch (error) {
            this.showAlert('Failed to load group by description data: ' + error.message, 'danger');
            this.showEmptyState('group-by-description');
        }
    }

    displayGroupByDescription(data) {
        this.hideLoading('group-by-description');
        this.hideEmptyState('group-by-description');
        
        const results = document.getElementById('group-by-description-results');
        const tbody = document.getElementById('description-group-body');
        
        if (results && tbody) {
            results.style.display = 'block';
            
            tbody.innerHTML = data.groups.map(group => `
                <tr>
                    <td>${group.description}</td>
                    <td>${group.count}</td>
                    <td>$${group.total_amount.toFixed(2)}</td>
                    <td>$${group.average_amount.toFixed(2)}</td>
                    <td>$${group.min_amount.toFixed(2)}</td>
                    <td>$${group.max_amount.toFixed(2)}</td>
                </tr>
            `).join('');
        }
    }

    async loadMonthlySummary() {
        if (!this.currentFile) {
            this.showEmptyState('monthly-summary');
            return;
        }

        this.showLoading('monthly-summary');
        
        try {
            const response = await fetch(`/api/files/analytics/${this.config.source}/monthly-summary?fileType=${this.currentFile.type}&filePath=${encodeURIComponent(this.currentFile.path)}`);
            
            if (response.ok) {
                const data = await response.json();
                this.displayMonthlySummary(data);
            } else {
                throw new Error('Failed to load monthly summary data');
            }
        } catch (error) {
            this.showAlert('Failed to load monthly summary data: ' + error.message, 'danger');
            this.showEmptyState('monthly-summary');
        }
    }

    displayMonthlySummary(data) {
        this.hideLoading('monthly-summary');
        this.hideEmptyState('monthly-summary');
        
        const results = document.getElementById('monthly-summary-results');
        const stats = document.getElementById('monthly-summary-stats');
        
        if (results && stats) {
            results.style.display = 'block';
            
            // Display statistics
            stats.innerHTML = `
                <div class="mb-3">
                    <strong>Total Transactions:</strong> ${data.total_transactions}
                </div>
                <div class="mb-3">
                    <strong>Total Amount:</strong> $${data.total_amount.toFixed(2)}
                </div>
                <div class="mb-3">
                    <strong>Average per Month:</strong> $${data.average_per_month.toFixed(2)}
                </div>
                <div class="mb-3">
                    <strong>Highest Month:</strong> ${data.highest_month}
                </div>
            `;
            
            // Create chart
            this.createMonthlyChart(data.monthly_data);
        }
    }

    createMonthlyChart(monthlyData) {
        const ctx = document.getElementById('monthly-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.monthly) {
            this.charts.monthly.destroy();
        }

        this.charts.monthly = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthlyData.map(d => d.month),
                datasets: [{
                    label: 'Total Amount',
                    data: monthlyData.map(d => d.amount),
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Amount: $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }

    async loadAmountAnalysis() {
        if (!this.currentFile) {
            this.showEmptyState('amount-analysis');
            return;
        }

        this.showLoading('amount-analysis');
        
        try {
            const response = await fetch(`/api/files/analytics/${this.config.source}/amount-analysis?fileType=${this.currentFile.type}&filePath=${encodeURIComponent(this.currentFile.path)}`);
            
            if (response.ok) {
                const data = await response.json();
                this.displayAmountAnalysis(data);
            } else {
                throw new Error('Failed to load amount analysis data');
            }
        } catch (error) {
            this.showAlert('Failed to load amount analysis data: ' + error.message, 'danger');
            this.showEmptyState('amount-analysis');
        }
    }

    displayAmountAnalysis(data) {
        this.hideLoading('amount-analysis');
        this.hideEmptyState('amount-analysis');
        
        const results = document.getElementById('amount-analysis-results');
        const stats = document.getElementById('amount-statistics');
        
        if (results && stats) {
            results.style.display = 'block';
            
            // Display statistics
            stats.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <strong>Mean Amount:</strong> $${data.mean.toFixed(2)}
                        </div>
                        <div class="mb-3">
                            <strong>Median Amount:</strong> $${data.median.toFixed(2)}
                        </div>
                        <div class="mb-3">
                            <strong>Standard Deviation:</strong> $${data.std_dev.toFixed(2)}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <strong>Min Amount:</strong> $${data.min.toFixed(2)}
                        </div>
                        <div class="mb-3">
                            <strong>Max Amount:</strong> $${data.max.toFixed(2)}
                        </div>
                        <div class="mb-3">
                            <strong>Total Transactions:</strong> ${data.count}
                        </div>
                    </div>
                </div>
            `;
            
            // Create charts
            this.createAmountDistributionChart(data.distribution);
            this.createAmountRangeChart(data.ranges);
        }
    }

    createAmountDistributionChart(distribution) {
        const ctx = document.getElementById('amount-distribution-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.amountDistribution) {
            this.charts.amountDistribution.destroy();
        }

        this.charts.amountDistribution = new Chart(ctx, {
            type: 'line',
            data: {
                labels: distribution.map(d => d.range),
                datasets: [{
                    label: 'Frequency',
                    data: distribution.map(d => d.count),
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Amount Distribution'
                    }
                }
            }
        });
    }

    createAmountRangeChart(ranges) {
        const ctx = document.getElementById('amount-range-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.amountRange) {
            this.charts.amountRange.destroy();
        }

        this.charts.amountRange = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ranges.map(d => d.range),
                datasets: [{
                    data: ranges.map(d => d.count),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Amount Ranges'
                    }
                }
            }
        });
    }

    async loadTrends() {
        if (!this.currentFile) {
            this.showEmptyState('trends');
            return;
        }

        this.showLoading('trends');
        
        try {
            const response = await fetch(`/api/files/analytics/${this.config.source}/trends?fileType=${this.currentFile.type}&filePath=${encodeURIComponent(this.currentFile.path)}`);
            
            if (response.ok) {
                const data = await response.json();
                this.displayTrends(data);
            } else {
                throw new Error('Failed to load trends data');
            }
        } catch (error) {
            this.showAlert('Failed to load trends data: ' + error.message, 'danger');
            this.showEmptyState('trends');
        }
    }

    displayTrends(data) {
        this.hideLoading('trends');
        this.hideEmptyState('trends');
        
        const results = document.getElementById('trends-results');
        const insights = document.getElementById('trend-insights');
        
        if (results && insights) {
            results.style.display = 'block';
            
            // Display insights
            insights.innerHTML = `
                <div class="mb-3">
                    <strong>Trend Direction:</strong> ${data.trend_direction}
                </div>
                <div class="mb-3">
                    <strong>Growth Rate:</strong> ${data.growth_rate}%
                </div>
                <div class="mb-3">
                    <strong>Peak Month:</strong> ${data.peak_month}
                </div>
                <div class="mb-3">
                    <strong>Lowest Month:</strong> ${data.lowest_month}
                </div>
            `;
            
            // Create trend chart
            this.createTrendsChart(data.trend_data);
        }
    }

    createTrendsChart(trendData) {
        const ctx = document.getElementById('trends-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.trends) {
            this.charts.trends.destroy();
        }

        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendData.map(d => d.month),
                datasets: [{
                    label: 'Amount Trend',
                    data: trendData.map(d => d.amount),
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Amount Trends Over Time'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }

    filterDescriptionTable(searchTerm) {
        const tbody = document.getElementById('description-group-body');
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr');
        rows.forEach(row => {
            const description = row.cells[0].textContent.toLowerCase();
            if (description.includes(searchTerm.toLowerCase())) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    exportDescriptionData() {
        if (!this.currentFile) return;

        // Create CSV content
        const tbody = document.getElementById('description-group-body');
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr');
        let csv = 'Description,Count,Total Amount,Average Amount,Min Amount,Max Amount\n';
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            const rowData = Array.from(cells).map(cell => cell.textContent.replace(',', ';'));
            csv += rowData.join(',') + '\n';
        });

        // Download file
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.config.sourceName}_description_analysis.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    showLoading(tabName) {
        const loading = document.getElementById(`${tabName}-loading`);
        const results = document.getElementById(`${tabName}-results`);
        const empty = document.getElementById(`${tabName}-empty`);
        
        if (loading) loading.style.display = 'block';
        if (results) results.style.display = 'none';
        if (empty) empty.style.display = 'none';
    }

    hideLoading(tabName) {
        const loading = document.getElementById(`${tabName}-loading`);
        if (loading) loading.style.display = 'none';
    }

    showEmptyState(tabName) {
        const loading = document.getElementById(`${tabName}-loading`);
        const results = document.getElementById(`${tabName}-results`);
        const empty = document.getElementById(`${tabName}-empty`);
        
        if (loading) loading.style.display = 'none';
        if (results) results.style.display = 'none';
        if (empty) empty.style.display = 'block';
    }

    hideEmptyState(tabName) {
        const empty = document.getElementById(`${tabName}-empty`);
        if (empty) empty.style.display = 'none';
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
}

// Initialize the analytics app when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.sourceAnalyticsApp = new SourceAnalyticsApp();
}); 