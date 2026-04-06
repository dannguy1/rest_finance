# Bank Statement Analytics

## Overview

The Bank Statement Analytics page provides six analysis tabs for any processed bank source file (Bank of America, Chase, etc.). Navigate to a bank statement via the location-centric sidebar, select a processed file, then click **Analytics** to open the analytics view.

| Tab | Description |
|-----|-------------|
| Group by Description | Aggregate totals grouped by unique description strings |
| Monthly Summary | Month-by-month income, charges, and net amounts |
| Amount Analysis | Distribution of transaction amounts |
| Trends | Rolling trend and growth-rate charts |
| Merchant Analysis | Card-processing deposits and charges (pattern-based) |
| Payroll | Payroll transfer transactions (pattern-based) |

---

## Pattern-Based Analysis

Merchant Analysis and Payroll both use a **pattern-based filter** to identify relevant transactions from the bank statement. Each bank source has its own patterns because different banks format transaction descriptions differently.

### How It Works

1. The analytics endpoint loads the processed bank CSV.
2. For each pattern-based tab, it looks up the bank source's pattern from `SOURCE_CONFIGS` in `app/api/routes/analytics_routes.py`.
3. It applies the filter to the `Description` column and returns matching rows with a summary and monthly breakdown.

### Pattern Configuration

Patterns live inside `SOURCE_CONFIGS` in `app/api/routes/analytics_routes.py`:

```python
SOURCE_CONFIGS = {
    "bankofamerica": {
        "name": "BankOfAmerica",
        ...
        "merchant_pattern": {
            "type": "prefix",        # match mode (see below)
            "value": "BANKCARD 8076",
            "label": "Merchant Deposits & Charges (BANKCARD 8076)"
        },
        "payroll_pattern": {
            "type": "contains",
            "value": "Online Banking transfer to CHK 8068",
            "label": "Payroll Transfers (CHK 8068)"
        }
    },
    "chase": {
        "name": "Chase",
        ...
        "merchant_pattern": {
            "type": "contains",
            "value": "BANKCARD 8076",
            "label": "Merchant Deposits & Charges (BANKCARD 8076)"
        },
        "payroll_pattern": {
            "type": "contains",
            "value": "Online Transfer to CHK",
            "label": "Payroll Transfers (CHK ...2276)"
        }
    }
}
```

### Match Types

| Type | Behaviour | Use When |
|------|-----------|----------|
| `prefix` | Description **starts with** the value | Bank always places identifier at the beginning (e.g. BofA BANKCARD) |
| `contains` | Description **contains** the value anywhere (case-insensitive) | Identifier appears anywhere in the description (e.g. Chase) |
| `suffix` | Description **ends with** the value | Identifier always appears at the end |
| `regex` | Full Python regex applied to description (case-insensitive) | Complex or multi-variant patterns that can't be expressed as a fixed string |

The `label` field is shown as a badge in the UI so the user knows which filter was applied.

---

## How to Add a New Pattern Category

Follow these four steps to add a completely new analysis tab (e.g. "Rent", "Utilities", "Insurance").

### Step 1 — Add the pattern to `SOURCE_CONFIGS`

Open `app/api/routes/analytics_routes.py` and add a new key to each bank source that should support the analysis:

```python
"bankofamerica": {
    ...
    "rent_pattern": {
        "type": "contains",
        "value": "PROPERTY MGMT",
        "label": "Rent Payments (PROPERTY MGMT)"
    }
},
"chase": {
    ...
    "rent_pattern": {
        "type": "contains",
        "value": "PROP MGMT",
        "label": "Rent Payments (PROP MGMT)"
    }
}
```

> Sources that do **not** have the pattern key will return HTTP 422 with a "not configured" message — the UI shows a "Not Available" state rather than crashing.

### Step 2 — Add the API endpoint

In the same file, add a new route that calls `_pattern_analysis()` with your pattern key:

```python
@router.get("/{source}/rent-analysis")
@limiter.limit(settings.rate_limit_api)
@handle_service_errors
async def analytics_rent_analysis(
    source: str,
    request: Request,
    fileType: str = Query(..., description="Type of file (processed or uploaded)"),
    filePath: str = Query(..., description="Path to the file")
):
    """Extract rent/property payment transactions."""
    return await _pattern_analysis(source, fileType, filePath, "rent_pattern", "Rent Analysis")
```

### Step 3 — Add the HTML tab

Open `app/templates/source_analytics.html`. Add a tab button inside the `<ul class="nav nav-tabs">` block:

```html
<li class="nav-item" role="presentation">
    <button class="nav-link" id="rent-analysis-tab"
            data-bs-toggle="tab" data-bs-target="#rent-analysis-pane"
            type="button" role="tab">
        <i class="bi bi-house me-2"></i>
        Rent
    </button>
</li>
```

Add the tab pane after the last existing pane (before the closing `</div>` of `tab-content`). Copy the Payroll pane block and replace every `payroll` ID/class reference with `rent`:

```html
<!-- Rent Analysis Tab -->
<div class="tab-pane fade" id="rent-analysis-pane" role="tabpanel"
     aria-labelledby="rent-analysis-tab" tabindex="0">
    <div class="row"><div class="col-12">
        <div class="card border-0 shadow-sm">
            <div class="card-header text-white d-flex justify-content-between align-items-center"
                 style="background-color:#0dcaf0;">
                <h5 class="mb-0"><i class="bi bi-house me-2"></i>Rent Analysis</h5>
                <button class="btn btn-sm btn-outline-light" id="export-rent-data">
                    <i class="bi bi-download me-1"></i>Export CSV
                </button>
            </div>
            <div class="card-body">
                <div class="text-center py-5" id="rent-loading" style="display:none;">
                    <div class="spinner-border" role="status"></div>
                    <p class="mt-2 text-muted">Analyzing rent transactions...</p>
                </div>
                <div id="rent-results" style="display:none;">
                    <!-- pattern badge, summary cards, monthly table, txn table -->
                    <!-- (copy structure from payroll pane, replace IDs) -->
                </div>
                <div class="text-center py-5" id="rent-unavailable" style="display:none;">
                    <i class="bi bi-slash-circle fs-1 text-muted mb-3"></i>
                    <h5 class="text-muted">Not Available</h5>
                    <p class="text-muted" id="rent-unavailable-msg">
                        Rent Analysis is not configured for this source.
                    </p>
                </div>
                <div class="text-center py-5" id="rent-empty">
                    <i class="bi bi-file-earmark-text fs-1 text-muted mb-3"></i>
                    <h5 class="text-muted">No file selected</h5>
                    <p class="text-muted">Select a file to analyze rent payments.</p>
                </div>
            </div>
        </div>
    </div></div>
</div>
```

> **Required element IDs** (replace `rent` with your category name throughout):
> - `{name}-loading` — spinner shown while fetching
> - `{name}-results` — shown when data loads successfully
> - `{name}-unavailable` — shown when source has no pattern configured
> - `{name}-unavailable-msg` — paragraph updated with server error detail
> - `{name}-empty` — shown before a file is selected
> - `{name}-pattern-label` — text node for the filter badge
> - `{name}-total-count`, `{name}-monthly-tbody`, `{name}-monthly-tfoot`, `{name}-txn-count-badge`, `{name}-txn-tbody`

### Step 4 — Add the JavaScript methods

Open `app/static/js/source_analytics.js`.

**Wire the tab click** (inside the `show.bs.tab` listener):

```js
} else if (e.target.id === 'rent-analysis-tab') {
    this.loadRentAnalysis();
}
```

**Wire the export button** (inside `setupEventListeners`):

```js
const exportRentBtn = document.getElementById('export-rent-data');
if (exportRentBtn) exportRentBtn.addEventListener('click', () => this.exportRentData());
```

**Add the three methods** (after `exportPayrollData()`):

```js
// ── Rent Analysis ─────────────────────────────────────────────────────────

async loadRentAnalysis() {
    if (!this.currentFile) { this.showEmptyState('rent'); return; }
    this.showLoading('rent');
    try {
        const url = `/api/files/analytics/${this.config.source}/rent-analysis`
            + `?fileType=${this.currentFile.type}`
            + `&filePath=${encodeURIComponent(this.currentFile.path)}`;
        const response = await fetch(url);
        if (response.status === 422) {
            const err = await response.json();
            this.hideLoading('rent');
            document.getElementById('rent-empty').style.display = 'none';
            document.getElementById('rent-unavailable').style.display = 'block';
            const msg = document.getElementById('rent-unavailable-msg');
            if (msg) msg.textContent = err.detail || 'Rent Analysis is not configured.';
            return;
        }
        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        const data = await response.json();
        this._rentData = data;
        this.displayRentAnalysis(data);
    } catch (err) {
        this.hideLoading('rent');
        this.showAlert('Failed to load rent analysis: ' + err.message, 'danger');
        this.showEmptyState('rent');
    }
}

displayRentAnalysis(data) {
    this.hideLoading('rent');
    document.getElementById('rent-empty').style.display = 'none';
    document.getElementById('rent-unavailable').style.display = 'none';
    document.getElementById('rent-results').style.display = 'block';

    document.getElementById('rent-pattern-label').textContent =
        data.pattern?.label || data.pattern?.value || 'Rent Filter';

    const s = data.summary;
    // populate summary card elements (total_income, total_charges, net, total_count)

    // monthly table
    const monthTbody = document.getElementById('rent-monthly-tbody');
    monthTbody.innerHTML = data.monthly_breakdown.map(m => `<tr>
        <td>${this._escapeHtml(m.label)}</td>
        <td class="text-end text-success">$${m.income.toFixed(2)}</td>
        <td class="text-end text-danger">$${Math.abs(m.charges).toFixed(2)}</td>
        <td class="text-end">$${m.net.toFixed(2)}</td>
        <td class="text-center">${m.count}</td>
    </tr>`).join('');

    // transaction table
    document.getElementById('rent-txn-count-badge').textContent = data.transactions.length;
    document.getElementById('rent-txn-tbody').innerHTML = data.transactions.map(t => `<tr>
        <td>${this._escapeHtml(t.date || '—')}</td>
        <td>${this._escapeHtml(t.description)}</td>
        <td class="text-end ${t.amount >= 0 ? 'text-success' : 'text-danger'}">
            ${t.amount < 0 ? '-' : ''}$${Math.abs(t.amount).toFixed(2)}</td>
        <td class="text-center">
            <span class="badge ${t.type === 'income' ? 'bg-success' : 'bg-danger'}">
                ${t.type === 'income' ? 'Credit' : 'Debit'}
            </span>
        </td>
    </tr>`).join('');
}

exportRentData() {
    if (!this._rentData) return;
    const rows = [['Date', 'Description', 'Amount', 'Type']];
    this._rentData.transactions.forEach(t =>
        rows.push([t.date, t.description, t.amount.toFixed(2), t.type]));
    const csv = rows.map(r =>
        r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = `${this.config.sourceName}_rent_analysis.csv`;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
}
```

---

## How to Add a New Bank Source

To support pattern analysis on a completely new bank (e.g. "Wells Fargo"):

1. Add the bank source entry to `SOURCE_CONFIGS` with the appropriate patterns:

```python
"wellsfargo": {
    "name": "WellsFargo",
    "icon": "bank",
    "description": "Wells Fargo bank statement processing",
    "merchant_pattern": {
        "type": "contains",
        "value": "CARD SERVICES",
        "label": "Merchant Deposits (CARD SERVICES)"
    },
    "payroll_pattern": {
        "type": "contains",
        "value": "TRANSFER TO CHECKING",
        "label": "Payroll Transfers"
    }
}
```

2. Add the source to `app/config/location_config.py` if it belongs to a location.
3. Add the source mapping JSON to `config/wellsfargo.json` (see `docs/mapping.md`).
4. The analytics endpoints (`merchant-analysis`, `payroll-analysis`) will automatically work for the new source.

---

## API Reference

All analytics endpoints share the same query parameter contract:

| Parameter | Type | Description |
|-----------|------|-------------|
| `fileType` | string | `"processed"` or `"uploaded"` |
| `filePath` | string | Relative path to the CSV file |

| Endpoint | Description |
|----------|-------------|
| `GET /api/files/analytics/{source}/merchant-analysis` | Merchant card deposits and charges |
| `GET /api/files/analytics/{source}/payroll-analysis` | Payroll transfer transactions |

**Response shape** (same for all pattern-based endpoints):

```json
{
  "source": "BankOfAmerica",
  "file_type": "processed",
  "file_path": "data/bankofamerica/output/2025/01_2025.csv",
  "pattern": {
    "type": "contains",
    "value": "BANKCARD 8076",
    "label": "Merchant Deposits & Charges (BANKCARD 8076)"
  },
  "summary": {
    "total_income": 45231.50,
    "total_charges": -312.00,
    "net": 44919.50,
    "income_count": 22,
    "charge_count": 3,
    "total_count": 25
  },
  "monthly_breakdown": [
    {
      "month": "2025-01",
      "label": "Jan 2025",
      "income": 45231.50,
      "charges": -312.00,
      "net": 44919.50,
      "income_count": 22,
      "charge_count": 3,
      "count": 25
    }
  ],
  "transactions": [
    {
      "date": "2025-01-03",
      "description": "BANKCARD 8076    DES:BTOT DEP   ID:...",
      "amount": 2150.00,
      "type": "income"
    }
  ]
}
```

**Error responses:**

| Status | Meaning |
|--------|---------|
| 422 | Pattern not configured for this source (UI shows "Not Available") |
| 422 | File missing required `Description` or `Amount` columns |
| 404 | File not found |
