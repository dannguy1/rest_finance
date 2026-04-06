/**
 * Deposit Verification page controller.
 * Fetches verification configs and runs the matching algorithm via the API.
 */
'use strict';

const Verification = (() => {
    let _configs = [];
    let _availableMonths = [];   // [{year, month}, ...]
    let _lastResult = null;

    const MONTH_NAMES = [
        '', 'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    // ------------------------------------------------------------------
    // Init
    // ------------------------------------------------------------------
    async function init() {
        await _loadConfigs();
        _bindEvents();
    }

    async function _loadConfigs() {
        try {
            const resp = await fetch('/api/verification/configs');
            if (!resp.ok) throw new Error('Failed to load configs');
            const data = await resp.json();
            _configs = data.configs || [];
            _populateLocationSelect();
        } catch (e) {
            _showError('Could not load verification configurations: ' + e.message);
        }
    }

    function _populateLocationSelect() {
        const sel = document.getElementById('location-select');
        sel.innerHTML = '<option value="">Select location…</option>';
        _configs.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.location_id;
            opt.textContent = c.display_name;
            sel.appendChild(opt);
        });
    }

    // ------------------------------------------------------------------
    // Event bindings
    // ------------------------------------------------------------------
    function _bindEvents() {
        document.getElementById('location-select').addEventListener('change', _onLocationChange);
        document.getElementById('year-select').addEventListener('change', _onYearChange);
        document.getElementById('month-select').addEventListener('change', _onMonthChange);
        document.getElementById('run-btn').addEventListener('click', _runVerification);
        document.getElementById('export-btn').addEventListener('click', _exportCSV);
    }

    async function _onLocationChange() {
        const locId = document.getElementById('location-select').value;
        const yearSel = document.getElementById('year-select');
        const monthSel = document.getElementById('month-select');
        const runBtn = document.getElementById('run-btn');
        const infoEl = document.getElementById('source-info');

        yearSel.disabled = true; yearSel.innerHTML = '<option value="">—</option>';
        monthSel.disabled = true; monthSel.innerHTML = '<option value="">—</option>';
        runBtn.disabled = true;
        infoEl.innerHTML = '';

        if (!locId) return;

        const cfg = _configs.find(c => c.location_id === locId);
        if (cfg) {
            infoEl.innerHTML =
                `<i class="bi bi-receipt me-1"></i>Merchant: <strong>${cfg.merchant_source}</strong>` +
                `&nbsp;&nbsp;<i class="bi bi-bank me-1"></i>Bank: <strong>${cfg.bank_source}</strong>`;
        }

        try {
            const resp = await fetch(`/api/verification/${locId}/available-months`);
            const data = await resp.json();
            _availableMonths = data.months || [];
            _populateYearSelect();
        } catch (e) {
            _showError('Could not load available months: ' + e.message);
        }
    }

    function _populateYearSelect() {
        const yearSel = document.getElementById('year-select');
        const years = [...new Set(_availableMonths.map(m => m.year))].sort((a,b) => b - a);
        yearSel.innerHTML = '<option value="">Select year…</option>';
        years.forEach(y => {
            const opt = document.createElement('option');
            opt.value = y;
            opt.textContent = y;
            yearSel.appendChild(opt);
        });
        yearSel.disabled = years.length === 0;
    }

    function _onYearChange() {
        const year = parseInt(document.getElementById('year-select').value);
        const monthSel = document.getElementById('month-select');
        monthSel.disabled = true;
        monthSel.innerHTML = '<option value="">Select month…</option>';
        document.getElementById('run-btn').disabled = true;

        if (!year) return;
        const months = _availableMonths.filter(m => m.year === year).map(m => m.month).sort((a,b) => a - b);
        months.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = MONTH_NAMES[m];
            monthSel.appendChild(opt);
        });
        monthSel.disabled = months.length === 0;
    }

    function _onMonthChange() {
        const month = document.getElementById('month-select').value;
        document.getElementById('run-btn').disabled = !month;
    }

    // ------------------------------------------------------------------
    // Run verification
    // ------------------------------------------------------------------
    async function _runVerification() {
        const locId  = document.getElementById('location-select').value;
        const year   = document.getElementById('year-select').value;
        const month  = document.getElementById('month-select').value;
        if (!locId || !year || !month) return;

        const btn = document.getElementById('run-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Running…';

        _hideError();
        document.getElementById('results-section').classList.add('d-none');
        document.getElementById('empty-state').classList.add('d-none');

        try {
            const resp = await fetch(`/api/verification/${locId}/${year}/${month}`);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || 'Verification failed');
            _lastResult = data;
            _renderResults(data);
        } catch (e) {
            _showError(e.message);
            document.getElementById('empty-state').classList.remove('d-none');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-play-fill me-1"></i> Run Verification';
        }
    }

    // ------------------------------------------------------------------
    // Render
    // ------------------------------------------------------------------
    function _renderResults(data) {
        _renderSummaryCards(data.summary, data.display_name, data.year, data.month);
        _renderDayTable(data.day_summaries, data.matched_pairs);
        _renderUnmatched(data.unmatched_batches, data.unmatched_deposits);
        document.getElementById('results-section').classList.remove('d-none');
        document.getElementById('empty-state').classList.add('d-none');
    }

    function _renderSummaryCards(s, name, year, month) {
        const matchRate = s.match_rate;
        const matchClass = matchRate >= 100 ? 'text-success' : matchRate >= 90 ? 'text-warning' : 'text-danger';
        const matchIcon  = matchRate >= 100 ? 'bi-check-circle-fill' : matchRate >= 90 ? 'bi-exclamation-circle-fill' : 'bi-x-circle-fill';

        const html = `
        <div class="col-12 mb-2">
          <h5 class="text-muted">${name} — ${MONTH_NAMES[month]} ${year}</h5>
        </div>
        <div class="col-md-3">
          <div class="card stat-card matched p-3 h-100">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <div class="text-muted small mb-1">Match Rate</div>
                <div class="fs-3 fw-bold ${matchClass}">
                  <i class="bi ${matchIcon} me-1"></i>${matchRate}%
                </div>
                <div class="text-muted small">${s.matched_count} of ${s.total_merchant_batches} batches</div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card stat-card merchant p-3 h-100">
            <div class="text-muted small mb-1">Merchant Total</div>
            <div class="fs-4 fw-bold text-primary">${_fmt(s.total_merchant_amount)}</div>
            <div class="text-muted small">
              ${s.total_merchant_batches} batches + ${s.total_adjustments} adj.
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card stat-card bank p-3 h-100">
            <div class="text-muted small mb-1">Bank Deposits (matched)</div>
            <div class="fs-4 fw-bold text-purple" style="color:#6f42c1">${_fmt(s.matched_amount)}</div>
            <div class="text-muted small">
              ${s.total_bank_deposits} total deposits, ${s.unmatched_bank_count} unmatched
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card stat-card variance p-3 h-100">
            <div class="text-muted small mb-1">Unmatched Merchant</div>
            <div class="fs-4 fw-bold ${s.unmatched_merchant_count > 0 ? 'text-danger' : 'text-success'}">
              ${s.unmatched_merchant_count > 0 ? '⚠ ' + _fmt(s.unmatched_merchant_amount) : '✓ None'}
            </div>
            <div class="text-muted small">${s.unmatched_merchant_count} batches missing deposit</div>
          </div>
        </div>`;

        document.getElementById('summary-cards').innerHTML = html;

        const pct = Math.min(matchRate, 100);
        document.getElementById('match-progress').style.width = pct + '%';
        document.getElementById('match-rate-label').textContent = matchRate + '%';
    }

    function _renderDayTable(days, allPairs) {
        // Index matched pairs by sale_date for drill-down
        const pairsByDate = {};
        allPairs.forEach(p => {
            (pairsByDate[p.sale_date] = pairsByDate[p.sale_date] || []).push(p);
        });

        const tbody = document.getElementById('day-tbody');
        const tfoot = document.getElementById('day-tfoot');
        let totalMerchant = 0, totalBank = 0, totalBatches = 0, totalMatched = 0;
        let rows = '';

        days.forEach(d => {
            totalMerchant += d.merchant_total;
            totalBank     += d.bank_total;
            totalBatches  += d.merchant_batches;
            totalMatched  += d.matched_count;

            const badge = _statusBadge(d.status);
            const lag = d.deposit_date && d.sale_date
                ? _lagLabel(d.sale_date, d.deposit_date) : '—';
            const depDate = d.deposit_date
                ? _fmtDate(d.deposit_date) : '<span class="text-muted">—</span>';

            rows += `<tr class="day-row" data-sale-date="${d.sale_date}">
              <td>${_fmtDate(d.sale_date)}</td>
              <td class="text-end">${d.merchant_batches}</td>
              <td class="text-end">${_fmt(d.merchant_total)}</td>
              <td>${depDate}</td>
              <td class="text-end">${d.bank_deposits}</td>
              <td class="text-end">${d.bank_total > 0 ? _fmt(d.bank_total) : '<span class="text-muted">—</span>'}</td>
              <td class="text-end">${lag}</td>
              <td>${badge}</td>
              <td><button class="btn btn-sm btn-outline-secondary py-0 px-1" title="View detail">
                <i class="bi bi-zoom-in"></i></button></td>
            </tr>`;
        });

        tbody.innerHTML = rows;
        tfoot.innerHTML = `<tr>
          <td>Totals</td>
          <td class="text-end">${totalBatches}</td>
          <td class="text-end">${_fmt(totalMerchant)}</td>
          <td></td>
          <td class="text-end">${totalMatched}</td>
          <td class="text-end">${_fmt(totalBank)}</td>
          <td></td><td></td><td></td>
        </tr>`;

        // Drill-down click
        tbody.querySelectorAll('tr.day-row').forEach(row => {
            row.querySelector('button').addEventListener('click', (e) => {
                e.stopPropagation();
                const saleDate = row.dataset.saleDate;
                _openDrillDown(saleDate, days, pairsByDate[saleDate] || []);
            });
            row.addEventListener('click', (e) => {
                if (e.target.tagName === 'BUTTON' || e.target.tagName === 'I') return;
                const saleDate = row.dataset.saleDate;
                _openDrillDown(saleDate, days, pairsByDate[saleDate] || []);
            });
        });
    }

    function _renderUnmatched(batches, deposits) {
        document.getElementById('unmatched-batch-count').textContent = batches.length;
        document.getElementById('unmatched-dep-count').textContent = deposits.length;

        const bTbody = document.getElementById('unmatched-batches-tbody');
        if (batches.length === 0) {
            bTbody.innerHTML = '<tr><td colspan="3" class="text-center text-success py-2"><i class="bi bi-check-circle me-1"></i>All batches matched</td></tr>';
        } else {
            bTbody.innerHTML = batches.map(b => `<tr>
              <td>${_fmtDate(b.sale_date)}</td>
              <td class="font-monospace small">${_esc(b.ref)}</td>
              <td class="text-end text-danger">${_fmt(b.amount)}</td>
            </tr>`).join('');
        }

        const dTbody = document.getElementById('unmatched-deposits-tbody');
        if (deposits.length === 0) {
            dTbody.innerHTML = '<tr><td colspan="3" class="text-center text-success py-2"><i class="bi bi-check-circle me-1"></i>No extra deposits</td></tr>';
        } else {
            dTbody.innerHTML = deposits.map(d => `<tr>
              <td>${_fmtDate(d.deposit_date)}</td>
              <td class="text-end">${_fmt(d.amount)}</td>
              <td class="text-muted small">Other terminal</td>
            </tr>`).join('');
        }
    }

    // ------------------------------------------------------------------
    // Drill-down modal
    // ------------------------------------------------------------------
    function _openDrillDown(saleDate, allDays, pairs) {
        const day = allDays.find(d => d.sale_date === saleDate);
        if (!day) return;

        document.getElementById('modal-title-text').textContent =
            `${_fmtDate(saleDate)} — ${day.merchant_batches} batch${day.merchant_batches !== 1 ? 'es' : ''}`;

        // All batches from result for this day
        const result = _lastResult;
        const batchesForDay = [
            ...(result.matched_pairs.filter(p => p.sale_date === saleDate)),
            ...(result.unmatched_batches.filter(b => b.sale_date === saleDate)),
        ];

        const bTbody = document.getElementById('modal-batches-tbody');
        bTbody.innerHTML = batchesForDay.length === 0
            ? '<tr><td colspan="4" class="text-muted text-center">No batch data</td></tr>'
            : batchesForDay.map(b => {
                const isMatched = result.matched_pairs.some(p => p.sale_date === saleDate && p.merchant_ref === b.merchant_ref && p.amount === b.amount);
                const ref = b.merchant_ref || b.ref;
                const badge = isMatched
                    ? '<span class="badge bg-success">matched</span>'
                    : '<span class="badge bg-danger">missing</span>';
                return `<tr class="pair-row">
                  <td>${_fmtDate(saleDate)}</td>
                  <td class="font-monospace small">${_esc(ref)}</td>
                  <td class="text-end">${_fmt(b.amount)}</td>
                  <td>${badge}</td>
                </tr>`;
              }).join('');

        const dTbody = document.getElementById('modal-deposits-tbody');
        dTbody.innerHTML = pairs.length === 0
            ? '<tr><td colspan="3" class="text-danger text-center">No matching deposits found</td></tr>'
            : pairs.map(p => `<tr class="pair-row">
                <td>${_fmtDate(p.deposit_date)}</td>
                <td class="text-end">${_fmt(p.amount)}</td>
                <td class="font-monospace small">${_esc(p.merchant_ref)}</td>
              </tr>`).join('');

        const pTbody = document.getElementById('modal-pairs-tbody');
        pTbody.innerHTML = pairs.length === 0
            ? '<tr><td colspan="5" class="text-muted text-center">No matched pairs</td></tr>'
            : pairs.map(p => `<tr class="pair-row">
                <td>${_fmtDate(p.sale_date)}</td>
                <td class="font-monospace small">${_esc(p.merchant_ref)}</td>
                <td class="text-end">${_fmt(p.amount)}</td>
                <td>${_fmtDate(p.deposit_date)}</td>
                <td class="text-end">${p.lag_days} biz day${p.lag_days !== 1 ? 's' : ''}</td>
              </tr>`).join('');

        new bootstrap.Modal(document.getElementById('dayDetailModal')).show();
    }

    // ------------------------------------------------------------------
    // CSV export
    // ------------------------------------------------------------------
    function _exportCSV() {
        if (!_lastResult) return;
        const { day_summaries: days, display_name, year, month } = _lastResult;
        const header = 'Sale Date,Merchant Batches,Merchant Total,Deposit Date,Bank Deposits,Bank Total,Status\n';
        const rows = days.map(d =>
            `${d.sale_date},${d.merchant_batches},${d.merchant_total},${d.deposit_date || ''},${d.bank_deposits},${d.bank_total},${d.status}`
        ).join('\n');
        const blob = new Blob([header + rows], { type: 'text/csv' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `verification_${display_name.replace(/\s+/g, '_')}_${year}_${String(month).padStart(2,'0')}.csv`;
        a.click();
    }

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------
    function _statusBadge(status) {
        const map = {
            matched:    ['status-matched',    '✓ Matched'],
            partial:    ['status-partial',    '⚠ Partial'],
            missing:    ['status-missing',    '✗ Missing'],
            adjustment: ['status-adjustment', '~ Adj'],
        };
        const [cls, label] = map[status] || ['status-adjustment', status];
        return `<span class="status-badge ${cls}">${label}</span>`;
    }

    function _lagLabel(saleDate, depositDate) {
        // Simple calendar-day difference for display
        const diff = Math.round(
            (new Date(depositDate) - new Date(saleDate)) / 86400000
        );
        return `${diff}d`;
    }

    function _fmtDate(d) {
        if (!d) return '—';
        // Accept YYYY-MM-DD or MM/DD/YYYY
        const parts = String(d).includes('-') ? d.split('-') : null;
        if (parts) {
            return `${parts[1]}/${parts[2]}/${parts[0]}`;
        }
        return d;
    }

    function _fmt(n) {
        if (n === null || n === undefined) return '—';
        return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function _esc(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function _showError(msg) {
        document.getElementById('error-msg').textContent = msg;
        document.getElementById('error-state').classList.remove('d-none');
    }

    function _hideError() {
        document.getElementById('error-state').classList.add('d-none');
    }

    return { init };
})();

document.addEventListener('DOMContentLoaded', () => Verification.init());
