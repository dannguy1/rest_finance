class SourceAnalyticsApp {
    constructor() {
        this.config = window.sourceConfig;
        this.currentFile = null;
        this.charts = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDetailModal();
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
                } else if (e.target.id === 'merchant-analysis-tab') {
                    this.loadMerchantAnalysis();
                } else if (e.target.id === 'payroll-analysis-tab') {
                    this.loadPayrollAnalysis();
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

        const exportMerchantBtn = document.getElementById('export-merchant-data');
        if (exportMerchantBtn) {
            exportMerchantBtn.addEventListener('click', () => {
                this.exportMerchantData();
            });
        }

        const exportPayrollBtn = document.getElementById('export-payroll-data');
        if (exportPayrollBtn) {
            exportPayrollBtn.addEventListener('click', () => {
                this.exportPayrollData();
            });
        }
    }

    checkForSelectedFile() {
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
            
            tbody.innerHTML = data.groups.map(group => {
                const descEsc = this._escapeHtml(group.description);
                return `
                <tr>
                    <td>${descEsc}</td>
                    <td>${group.count}</td>
                    <td>$${group.total_amount.toFixed(2)}</td>
                    <td>$${group.average_amount.toFixed(2)}</td>
                    <td>$${group.min_amount.toFixed(2)}</td>
                    <td>$${group.max_amount.toFixed(2)}</td>
                    <td class="text-center">
                        <button class="btn btn-outline-primary btn-sm py-0 px-1 detail-btn"
                                title="View ${descEsc} transactions"
                                data-description="${descEsc}">
                            <i class="bi bi-eye"></i>
                            <span class="ms-1">${group.count}</span>
                        </button>
                    </td>
                </tr>`;
            }).join('');

            // Attach click handlers to detail buttons
            tbody.querySelectorAll('.detail-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    this.showDescriptionDetail(btn.dataset.description);
                });
            });
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
            
            // Check if this is GG data (has gross and net) or regular data (has total_amount)
            const isGGData = data.total_gross !== undefined && data.total_net !== undefined;
            
            // Display statistics
            if (isGGData) {
                stats.innerHTML = `
                    <div class="mb-3">
                        <strong>Total Transactions:</strong> ${data.total_transactions}
                    </div>
                    <div class="mb-3">
                        <strong>Total GROSS:</strong> $${data.total_gross.toFixed(2)}
                    </div>
                    <div class="mb-3">
                        <strong>Total NET:</strong> $${data.total_net.toFixed(2)}
                    </div>
                `;
            } else {
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
            }
            
            // Create chart
            this.createMonthlyChart(data.monthly_data, isGGData);
        }
    }

    createMonthlyChart(monthlyData, isGGData = false) {
        const ctx = document.getElementById('monthly-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.monthly) {
            this.charts.monthly.destroy();
        }

        if (isGGData) {
            // GG data has both gross and net
            this.charts.monthly = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: monthlyData.map(d => d.month),
                    datasets: [
                        {
                            label: 'GROSS',
                            data: monthlyData.map(d => d.gross),
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'NET',
                            data: monthlyData.map(d => d.net),
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }
                    ]
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
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    label += '$' + context.parsed.y.toFixed(2);
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
        } else {
            // Regular data has amount
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
                    <strong>Trend Direction:</strong> ${this._escapeHtml(data.trend_direction)}
                </div>
                <div class="mb-3">
                    <strong>Growth Rate:</strong> ${this._escapeHtml(String(data.growth_rate))}%
                </div>
                <div class="mb-3">
                    <strong>Peak Month:</strong> ${this._escapeHtml(data.peak_month)}
                </div>
                <div class="mb-3">
                    <strong>Lowest Month:</strong> ${this._escapeHtml(data.lowest_month)}
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

    setupDetailModal() {
        // Modal is created dynamically in showDescriptionDetail — nothing to do here
        this._detailData = null;
        this._detailModalInstance = null;
    }

    async showDescriptionDetail(description) {
        if (!this.currentFile) return;

        // Clean up any previous modal instance and its element
        if (this._detailModalInstance) {
            this._detailModalInstance.dispose();
            this._detailModalInstance = null;
        }
        const old = document.getElementById('descriptionDetailModal');
        if (old) old.remove();

        // Only remove backdrops left over from a previous detail modal (not other open modals)
        if (!document.querySelector('.modal.show')) {
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
            document.body.style.removeProperty('overflow');
            document.body.style.removeProperty('padding-right');
        }

        // Build modal HTML dynamically (matches source.js pattern)
        const modalHtml = `
        <div class="modal fade" id="descriptionDetailModal" tabindex="-1"
             aria-labelledby="descriptionDetailModalLabel" aria-modal="true" role="dialog"
             style="z-index:1060;">
            <div class="modal-dialog modal-xl modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="descriptionDetailModalLabel">
                            <i class="bi bi-list-ul me-2"></i>${this._escapeHtml(description)}
                        </h5>
                        <button type="button" class="btn-close btn-close-white"
                                data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center py-4" id="detail-modal-loading">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-2 text-muted">Loading transactions...</p>
                        </div>
                        <div id="detail-modal-summary" style="display:none;" class="mb-3">
                            <div class="row g-3">
                                <div class="col-sm-4">
                                    <div class="card border-0 bg-light text-center py-2">
                                        <div class="fs-5 fw-bold text-primary" id="detail-summary-count">—</div>
                                        <div class="small text-muted">Transactions</div>
                                    </div>
                                </div>
                                <div class="col-sm-4">
                                    <div class="card border-0 bg-light text-center py-2">
                                        <div class="fs-5 fw-bold text-success" id="detail-summary-total">—</div>
                                        <div class="small text-muted">Total Amount</div>
                                    </div>
                                </div>
                                <div class="col-sm-4">
                                    <div class="card border-0 bg-light text-center py-2">
                                        <div class="fs-5 fw-bold text-info" id="detail-summary-avg">—</div>
                                        <div class="small text-muted">Average Amount</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="detail-modal-table-wrapper" style="display:none;">
                            <div class="table-responsive">
                                <table class="table table-sm table-striped table-hover">
                                    <thead class="table-light sticky-top">
                                        <tr>
                                            <th>Date</th>
                                            <th>Description</th>
                                            <th class="text-end">Amount</th>
                                            <th id="detail-col-account" style="display:none;">Account</th>
                                            <th id="detail-col-simpledesc" style="display:none;">Simple Description</th>
                                        </tr>
                                    </thead>
                                    <tbody id="detail-modal-tbody"></tbody>
                                </table>
                            </div>
                        </div>
                        <div id="detail-modal-error" style="display:none;" class="alert alert-danger"></div>
                    </div>
                    <div class="modal-footer">
                        <span class="text-muted small me-auto">${this._escapeHtml(description)}</span>
                        <button type="button" class="btn btn-outline-secondary btn-sm"
                                id="detail-modal-export">
                            <i class="bi bi-download me-1"></i>Export CSV
                        </button>
                        <button type="button" class="btn btn-secondary"
                                data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalEl = document.getElementById('descriptionDetailModal');

        // Wire up export button
        document.getElementById('detail-modal-export')
            .addEventListener('click', () => this.exportDetailData());

        // Force reflow so Bootstrap can measure the element
        void modalEl.offsetWidth;

        // Create modal instance and show
        this._detailModalInstance = new bootstrap.Modal(modalEl, {
            backdrop: true,
            keyboard: true,
            focus: true
        });

        // Clean up element after modal closes; also abort any in-flight fetch
        const abortController = new AbortController();
        modalEl.addEventListener('hidden.bs.modal', () => {
            abortController.abort();
            if (this._detailModalInstance) {
                this._detailModalInstance.dispose();
                this._detailModalInstance = null;
            }
            modalEl.remove();
        }, { once: true });

        this._detailModalInstance.show();

        // Fetch data and populate
        try {
            const url = `/api/files/analytics/${this.config.source}/group-by-description/detail`
                + `?description=${encodeURIComponent(description)}`
                + `&fileType=${this.currentFile.type}`
                + `&filePath=${encodeURIComponent(this.currentFile.path)}`;

            const response = await fetch(url, { signal: abortController.signal });
            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            const data = await response.json();

            // Guard: modal may have been closed while fetching
            if (!document.getElementById('descriptionDetailModal')) return;

            this._detailData = data;

            document.getElementById('detail-summary-count').textContent = data.count;
            document.getElementById('detail-summary-total').textContent = `$${data.total_amount.toFixed(2)}`;
            const avg = data.count > 0 ? (data.total_amount / data.count) : 0;
            document.getElementById('detail-summary-avg').textContent   = `$${avg.toFixed(2)}`;

            const hasAccount    = data.records.some(r => r.account !== undefined);
            const hasSimpleDesc = data.records.some(r => r.simple_description !== undefined);

            document.getElementById('detail-col-account').style.display    = hasAccount    ? '' : 'none';
            document.getElementById('detail-col-simpledesc').style.display  = hasSimpleDesc ? '' : 'none';

            document.getElementById('detail-modal-tbody').innerHTML = data.records.map(r => {
                const amtClass = r.amount < 0 ? 'text-danger' : 'text-success';
                const sign     = r.amount < 0 ? '-' : '';
                let row = `<tr>
                    <td class="text-nowrap">${r.date || '—'}</td>
                    <td>${this._escapeHtml(r.description)}</td>
                    <td class="text-end ${amtClass}">${sign}$${Math.abs(r.amount).toFixed(2)}</td>`;
                if (hasAccount)    row += `<td>${this._escapeHtml(r.account || '')}</td>`;
                if (hasSimpleDesc) row += `<td>${this._escapeHtml(r.simple_description || '')}</td>`;
                row += `</tr>`;
                return row;
            }).join('');

            document.getElementById('detail-modal-loading').style.display      = 'none';
            document.getElementById('detail-modal-summary').style.display      = 'block';
            document.getElementById('detail-modal-table-wrapper').style.display = 'block';

        } catch (err) {
            // AbortError means the modal was closed before the fetch completed — ignore silently
            if (err.name === 'AbortError') return;
            const errorDiv = document.getElementById('detail-modal-error');
            if (!errorDiv) return;
            document.getElementById('detail-modal-loading').style.display = 'none';
            errorDiv.style.display = 'block';
            errorDiv.textContent   = 'Failed to load transactions: ' + err.message;
        }
    }

    // ── Merchant Analysis ────────────────────────────────────────────────────

    async loadMerchantAnalysis() {
        if (!this.currentFile) {
            this.showEmptyState('merchant');
            return;
        }
        this.showLoading('merchant');

        try {
            const url = `/api/files/analytics/${this.config.source}/merchant-analysis`
                + `?fileType=${this.currentFile.type}`
                + `&filePath=${encodeURIComponent(this.currentFile.path)}`;

            const response = await fetch(url);

            if (response.status === 422) {
                const err = await response.json();
                this.hideLoading('merchant');
                document.getElementById('merchant-empty').style.display = 'none';
                document.getElementById('merchant-unavailable').style.display = 'block';
                const msgEl = document.getElementById('merchant-unavailable-msg');
                if (msgEl) msgEl.textContent = err.detail || 'Merchant Analysis is not configured for this source.';
                return;
            }

            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            const data = await response.json();

            this._merchantData = data;
            this.displayMerchantAnalysis(data);
        } catch (err) {
            this.hideLoading('merchant');
            this.showAlert('Failed to load merchant analysis: ' + err.message, 'danger');
            this.showEmptyState('merchant');
        }
    }

    displayMerchantAnalysis(data) {
        this.hideLoading('merchant');
        document.getElementById('merchant-empty').style.display = 'none';
        document.getElementById('merchant-unavailable').style.display = 'none';
        document.getElementById('merchant-results').style.display = 'block';

        // Pattern badge
        const patternLabel = data.pattern?.label || data.pattern?.value || 'Merchant Filter';
        document.getElementById('merchant-pattern-label').textContent = patternLabel;

        // Summary cards
        const s = data.summary;
        document.getElementById('merchant-total-income').textContent  = `$${s.total_income.toFixed(2)}`;
        document.getElementById('merchant-total-charges').textContent = `$${Math.abs(s.total_charges).toFixed(2)}`;
        document.getElementById('merchant-income-count').textContent  = `${s.income_count} deposits`;
        document.getElementById('merchant-charge-count').textContent  = `${s.charge_count} charges`;
        document.getElementById('merchant-total-count').textContent   = s.total_count;

        const netEl = document.getElementById('merchant-net');
        netEl.textContent = `$${s.net.toFixed(2)}`;
        netEl.className = `fs-4 fw-bold ${s.net >= 0 ? 'text-success' : 'text-danger'}`;

        // Monthly breakdown table
        const monthTbody = document.getElementById('merchant-monthly-tbody');
        const monthTfoot = document.getElementById('merchant-monthly-tfoot');
        if (data.monthly_breakdown.length === 0) {
            monthTbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">No monthly data</td></tr>';
        } else {
            monthTbody.innerHTML = data.monthly_breakdown.map(m => {
                const netClass = m.net >= 0 ? 'text-success' : 'text-danger';
                return `<tr>
                    <td class="fw-semibold">${this._escapeHtml(m.label)}</td>
                    <td class="text-end text-success">$${m.income.toFixed(2)}</td>
                    <td class="text-end text-danger">$${Math.abs(m.charges).toFixed(2)}</td>
                    <td class="text-end ${netClass} fw-semibold">$${m.net.toFixed(2)}</td>
                    <td class="text-center">${m.count}</td>
                </tr>`;
            }).join('');
            // Totals footer
            monthTfoot.innerHTML = `<tr>
                <td>Total</td>
                <td class="text-end text-success">$${s.total_income.toFixed(2)}</td>
                <td class="text-end text-danger">$${Math.abs(s.total_charges).toFixed(2)}</td>
                <td class="text-end ${s.net >= 0 ? 'text-success' : 'text-danger'}">$${s.net.toFixed(2)}</td>
                <td class="text-center">${s.total_count}</td>
            </tr>`;
        }

        // Transaction table
        const txnCount = data.transactions.length;
        document.getElementById('merchant-txn-count-badge').textContent = txnCount;
        const txnTbody = document.getElementById('merchant-txn-tbody');
        if (txnCount === 0) {
            txnTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">No matching transactions found</td></tr>';
        } else {
            txnTbody.innerHTML = data.transactions.map(t => {
                const amtClass = t.amount >= 0 ? 'text-success' : 'text-danger';
                const sign     = t.amount < 0 ? '-' : '';
                const badge    = t.type === 'income'
                    ? '<span class="badge bg-success bg-opacity-75">Income</span>'
                    : '<span class="badge bg-danger bg-opacity-75">Charge</span>';
                return `<tr>
                    <td class="text-nowrap">${this._escapeHtml(t.date || '—')}</td>
                    <td>${this._escapeHtml(t.description)}</td>
                    <td class="text-end ${amtClass}">${sign}$${Math.abs(t.amount).toFixed(2)}</td>
                    <td class="text-center">${badge}</td>
                </tr>`;
            }).join('');
        }
    }

    exportMerchantData() {
        if (!this._merchantData) return;
        const d = this._merchantData;
        const rows = [['Date', 'Description', 'Amount', 'Type']];
        d.transactions.forEach(t => rows.push([t.date, t.description, t.amount.toFixed(2), t.type]));
        const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `${this.config.sourceName}_merchant_analysis.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // ── Payroll Analysis ─────────────────────────────────────────────────────

    async loadPayrollAnalysis() {
        if (!this.currentFile) {
            this.showEmptyState('payroll');
            return;
        }
        this.showLoading('payroll');

        try {
            const url = `/api/files/analytics/${this.config.source}/payroll-analysis`
                + `?fileType=${this.currentFile.type}`
                + `&filePath=${encodeURIComponent(this.currentFile.path)}`;

            const response = await fetch(url);

            if (response.status === 422) {
                const err = await response.json();
                this.hideLoading('payroll');
                document.getElementById('payroll-empty').style.display = 'none';
                document.getElementById('payroll-unavailable').style.display = 'block';
                const msgEl = document.getElementById('payroll-unavailable-msg');
                if (msgEl) msgEl.textContent = err.detail || 'Payroll Analysis is not configured for this source.';
                return;
            }

            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            const data = await response.json();

            this._payrollData = data;
            this.displayPayrollAnalysis(data);
        } catch (err) {
            this.hideLoading('payroll');
            this.showAlert('Failed to load payroll analysis: ' + err.message, 'danger');
            this.showEmptyState('payroll');
        }
    }

    displayPayrollAnalysis(data) {
        this.hideLoading('payroll');
        document.getElementById('payroll-empty').style.display = 'none';
        document.getElementById('payroll-unavailable').style.display = 'none';
        document.getElementById('payroll-results').style.display = 'block';

        // Pattern badge
        const patternLabel = data.pattern?.label || data.pattern?.value || 'Payroll Filter';
        document.getElementById('payroll-pattern-label').textContent = patternLabel;

        // Summary cards — payroll is almost always outflows (transfers out)
        const s = data.summary;
        const totalOut = Math.abs(s.total_charges);
        document.getElementById('payroll-total-transfers').textContent = `$${totalOut.toFixed(2)}`;
        document.getElementById('payroll-total-charges').textContent   = `$${totalOut.toFixed(2)}`;
        document.getElementById('payroll-transfer-count').textContent  = `${s.charge_count} transfers`;
        document.getElementById('payroll-charge-count').textContent    = `${s.charge_count} debits`;
        document.getElementById('payroll-total-count').textContent     = s.total_count;

        const netEl = document.getElementById('payroll-net');
        netEl.textContent = `$${s.net.toFixed(2)}`;
        netEl.className = `fs-4 fw-bold ${s.net >= 0 ? 'text-success' : 'text-danger'}`;

        // Monthly breakdown table
        const monthTbody = document.getElementById('payroll-monthly-tbody');
        const monthTfoot = document.getElementById('payroll-monthly-tfoot');
        if (data.monthly_breakdown.length === 0) {
            monthTbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">No monthly data</td></tr>';
        } else {
            monthTbody.innerHTML = data.monthly_breakdown.map(m => {
                const netClass = m.net >= 0 ? 'text-success' : 'text-danger';
                return `<tr>
                    <td class="fw-semibold">${this._escapeHtml(m.label)}</td>
                    <td class="text-end text-success">$${m.income.toFixed(2)}</td>
                    <td class="text-end text-danger">$${Math.abs(m.charges).toFixed(2)}</td>
                    <td class="text-end ${netClass} fw-semibold">$${m.net.toFixed(2)}</td>
                    <td class="text-center">${m.count}</td>
                </tr>`;
            }).join('');
            monthTfoot.innerHTML = `<tr>
                <td>Total</td>
                <td class="text-end text-success">$${s.total_income.toFixed(2)}</td>
                <td class="text-end text-danger">$${Math.abs(s.total_charges).toFixed(2)}</td>
                <td class="text-end ${s.net >= 0 ? 'text-success' : 'text-danger'}">$${s.net.toFixed(2)}</td>
                <td class="text-center">${s.total_count}</td>
            </tr>`;
        }

        // Transaction table
        const txnCount = data.transactions.length;
        document.getElementById('payroll-txn-count-badge').textContent = txnCount;
        const txnTbody = document.getElementById('payroll-txn-tbody');
        if (txnCount === 0) {
            txnTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">No payroll transactions found</td></tr>';
        } else {
            txnTbody.innerHTML = data.transactions.map(t => {
                const amtClass = t.amount >= 0 ? 'text-success' : 'text-danger';
                const sign     = t.amount < 0 ? '-' : '';
                const badge    = t.amount < 0
                    ? '<span class="badge" style="background-color:#6610f2;">Transfer Out</span>'
                    : '<span class="badge bg-success bg-opacity-75">Credit</span>';
                return `<tr>
                    <td class="text-nowrap">${this._escapeHtml(t.date || '—')}</td>
                    <td>${this._escapeHtml(t.description)}</td>
                    <td class="text-end ${amtClass}">${sign}$${Math.abs(t.amount).toFixed(2)}</td>
                    <td class="text-center">${badge}</td>
                </tr>`;
            }).join('');
        }
    }

    exportPayrollData() {
        if (!this._payrollData) return;
        const d = this._payrollData;
        const rows = [['Date', 'Description', 'Amount', 'Type']];
        d.transactions.forEach(t => rows.push([t.date, t.description, t.amount.toFixed(2), t.type]));
        const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `${this.config.sourceName}_payroll_analysis.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    _escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    exportDetailData() {
        if (!this._detailData) return;
        const d = this._detailData;
        const rows = [['Date', 'Description', 'Amount']];
        d.records.forEach(r => rows.push([r.date, r.description, r.amount.toFixed(2)]));
        const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `${this.config.sourceName}_${d.description.replace(/[^a-z0-9]/gi, '_')}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    exportDescriptionData() {
        if (!this.currentFile) return;

        // Create CSV content (skip the last Details column)
        const tbody = document.getElementById('description-group-body');
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr');
        let csv = 'Description,Count,Total Amount,Average Amount,Min Amount,Max Amount\n';
        
        rows.forEach(row => {
            const cells = Array.from(row.querySelectorAll('td')).slice(0, 6); // exclude Details column
            const rowData = cells.map(cell => `"${cell.textContent.trim().replace(/"/g, '""')}"`);
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