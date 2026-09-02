/**
 * FinAnalytics - Frontend Application Logic & AJAX Handlers
 */

let currentTable = 'Customer';
let currentPage = 1;
let currentSearch = '';
let chartsInstance = {};

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadDashboardStats();
    initCharts();
    loadPresetQueriesDropdown();
    loadTableData('Customer');
    loadCleaningAudit();
    loadVisualizationsGallery();
    loadExecutiveInsights();
});

// ── 1. Sidebar Navigation ───────────────────────────────────────────────────

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    const titles = {
        'dashboard': { title: 'Dashboard Overview', sub: 'Real-time banking metrics, customer demographics & system telemetry' },
        'database': { title: 'Database Explorer & Live SQL Console', sub: 'Run raw queries or browse clean relational SQLite tables' },
        'crud': { title: 'CRUD Operations Manager', sub: 'Interactive forms for real-time insert & deletion in banking.db' },
        'cleaning': { title: 'Data Quality & Preprocessing Audit', sub: 'Before vs after transformation logs & fuzzy logic reports' },
        'visualizations': { title: 'Matplotlib & Seaborn Analytics Gallery', sub: 'High-resolution charts generated directly by Python pipeline execution' },
        'insights': { title: 'Executive Banking Recommendations', sub: 'Strategic insights for fraud risk, VIP retention & liquidity balance' },
        'pipeline': { title: 'Pipeline Execution Console', sub: 'Live runner & log viewer for main.py execution' }
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            
            navItems.forEach(i => i.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            item.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
            
            if (titles[targetTab]) {
                document.getElementById('page-title').innerText = titles[targetTab].title;
                document.getElementById('page-subtitle').innerText = titles[targetTab].sub;
            }
        });
    });
}

// ── 2. Dashboard KPIs & Interactive Charts ─────────────────────────────────

async function loadDashboardStats() {
    try {
        const res = await fetch('/api/stats');
        const json = await res.json();
        if (json.status === 'success') {
            const d = json.data;
            document.getElementById('kpi-customers').innerText = d.customers.toLocaleString();
            document.getElementById('kpi-balance').innerText = '₹' + d.total_balance.toLocaleString('en-IN', { maximumFractionDigits: 0 });
            document.getElementById('kpi-txns').innerText = d.transactions.toLocaleString() + ' (₹' + (d.transaction_volume/100000).toFixed(1) + 'L)';
            document.getElementById('kpi-loans').innerText = d.loans.toLocaleString() + ' (₹' + (d.loan_amount/10000000).toFixed(2) + ' Cr)';
        }
    } catch (err) {
        console.error('Failed to load dashboard stats:', err);
    }
}

function refreshDashboard() {
    loadDashboardStats();
    loadTableData(currentTable);
}

async function initCharts() {
    // 1. Branch Customers
    try {
        const res1 = await fetch('/api/chart-data/branch_customers');
        const data1 = await res1.json();
        if (data1.status === 'success') {
            const ctx1 = document.getElementById('chartBranchCustomers').getContext('2d');
            chartsInstance.branch = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: data1.labels,
                    datasets: [{
                        label: 'Customer Count',
                        data: data1.datasets[0].data,
                        backgroundColor: 'rgba(6, 182, 212, 0.7)',
                        borderColor: '#06b6d4',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                    }
                }
            });
        }
    } catch (e) { console.error(e); }

    // 2. Account Types
    try {
        const res2 = await fetch('/api/chart-data/account_types');
        const data2 = await res2.json();
        if (data2.status === 'success') {
            const ctx2 = document.getElementById('chartAccountTypes').getContext('2d');
            chartsInstance.accounts = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: data2.labels,
                    datasets: [{
                        data: data2.datasets[0].data,
                        backgroundColor: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } }
                }
            });
        }
    } catch (e) { console.error(e); }

    // 3. Loan Categories
    try {
        const res3 = await fetch('/api/chart-data/loan_categories');
        const data3 = await res3.json();
        if (data3.status === 'success') {
            const ctx3 = document.getElementById('chartLoanCategories').getContext('2d');
            chartsInstance.loans = new Chart(ctx3, {
                type: 'line',
                data: {
                    labels: data3.labels,
                    datasets: [{
                        label: 'Total Loan Volume (₹)',
                        data: data3.datasets[0].data,
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.15)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 6,
                        pointBackgroundColor: '#8b5cf6'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                    }
                }
            });
        }
    } catch (e) { console.error(e); }
}

// ── 3. Database Table Explorer & SQL Runner ───────────────────────────────

function switchTable(tableName) {
    currentTable = tableName;
    currentPage = 1;
    document.querySelectorAll('.tbl-btn').forEach(btn => {
        btn.classList.toggle('active', btn.innerText === tableName);
    });
    loadTableData(tableName);
}

function handleTableSearch(val) {
    currentSearch = val;
    currentPage = 1;
    loadTableData(currentTable);
}

function changePage(delta) {
    currentPage += delta;
    if (currentPage < 1) currentPage = 1;
    loadTableData(currentTable);
}

async function loadTableData(tableName) {
    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');
    const info = document.getElementById('table-pagination-info');

    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">Loading data...</td></tr>';

    try {
        const url = `/api/tables/${tableName}?page=${currentPage}&limit=12&search=${encodeURIComponent(currentSearch)}`;
        const res = await fetch(url);
        const json = await res.json();

        if (json.status === 'success') {
            const cols = json.columns;
            const rows = json.data;

            // Render Header
            thead.innerHTML = cols.map(c => `<th>${c}</th>`).join('');

            // Render Body
            if (rows.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">No matching records found.</td></tr>';
            } else {
                tbody.innerHTML = rows.map(r => {
                    return '<tr>' + cols.map(c => `<td>${r[c] !== null ? r[c] : '<span style="color:#64748b">NULL</span>'}</td>`).join('') + '</tr>';
                }).join('');
            }

            info.innerText = `Showing page ${json.page} of ${json.total_pages} (${json.total} total rows)`;
            document.getElementById('btn-prev-page').disabled = (json.page <= 1);
            document.getElementById('btn-next-page').disabled = (json.page >= json.total_pages);
        }
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="10" style="color:var(--accent-rose)">Failed to fetch table data: ${err.message}</td></tr>`;
    }
}

async function loadPresetQueriesDropdown() {
    const sel = document.getElementById('preset-query-select');
    try {
        const res = await fetch('/api/preset-queries');
        const json = await res.json();
        if (json.status === 'success') {
            json.presets.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.sql;
                opt.innerText = p.title;
                sel.appendChild(opt);
            });
        }
    } catch (e) { console.error(e); }
}

function loadPresetQuery(sql) {
    if (sql) {
        document.getElementById('sql-input').value = sql;
        executeSQL();
    }
}

async function executeSQL() {
    const query = document.getElementById('sql-input').value.trim();
    if (!query) return;

    const timerSpan = document.getElementById('sql-timer');
    timerSpan.innerText = 'Running...';

    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;">Executing query...</td></tr>';

    try {
        const res = await fetch('/api/sql/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const json = await res.json();

        if (json.status === 'success') {
            timerSpan.innerText = `Executed in ${json.execution_time_ms} ms (${json.affected_rows} rows affected)`;
            if (json.is_select) {
                thead.innerHTML = json.columns.map(c => `<th>${c}</th>`).join('');
                if (json.data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;">Query returned 0 rows.</td></tr>';
                } else {
                    tbody.innerHTML = json.data.map(r => {
                        return '<tr>' + json.columns.map(c => `<td>${r[c] !== null ? r[c] : 'NULL'}</td>`).join('') + '</tr>';
                    }).join('');
                }
            } else {
                thead.innerHTML = '<th>Status</th><th>Affected Rows</th>';
                tbody.innerHTML = `<tr><td><span style="color:var(--accent-emerald)">DML Command Succeeded</span></td><td>${json.affected_rows}</td></tr>`;
            }
        } else {
            timerSpan.innerText = 'Execution error';
            tbody.innerHTML = `<tr><td colspan="10" style="color:var(--accent-rose); font-family:var(--font-code);">Error: ${json.message}</td></tr>`;
        }
    } catch (err) {
        timerSpan.innerText = 'Network error';
        tbody.innerHTML = `<tr><td colspan="10" style="color:var(--accent-rose)">${err.message}</td></tr>`;
    }
}

// ── 4. CRUD Handlers ───────────────────────────────────────────────────────

async function submitAddCustomer(e) {
    e.preventDefault();
    const payload = {
        customer_id: document.getElementById('crud-cust-id').value,
        name: document.getElementById('crud-cust-name').value,
        email: document.getElementById('crud-cust-email').value,
        phone: document.getElementById('crud-cust-phone').value,
        annual_income: document.getElementById('crud-cust-income').value,
        credit_score: document.getElementById('crud-cust-score').value
    };

    try {
        const res = await fetch('/api/crud/customer/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.status === 'success') {
            alert(json.message);
            document.getElementById('add-customer-form').reset();
            refreshDashboard();
        } else {
            alert('Error: ' + json.message);
        }
    } catch (err) {
        alert('Network Error: ' + err.message);
    }
}

async function submitDeleteCustomer() {
    const custId = document.getElementById('delete-cust-id').value.trim();
    if (!custId) {
        alert('Please enter a Customer ID to delete');
        return;
    }

    if (!confirm(`Are you sure you want to delete Customer ${custId}?`)) return;

    try {
        const res = await fetch(`/api/crud/customer/delete/${custId}`, { method: 'DELETE' });
        const json = await res.json();
        if (json.status === 'success') {
            alert(json.message);
            document.getElementById('delete-cust-id').value = '';
            refreshDashboard();
        } else {
            alert('Error: ' + json.message);
        }
    } catch (err) {
        alert('Network Error: ' + err.message);
    }
}

// ── 5. Data Quality Audit Audit Metrics ───────────────────────────────────

async function loadCleaningAudit() {
    const tbody = document.getElementById('cleaning-metrics-tbody');
    try {
        const res = await fetch('/api/cleaning_report');
        const json = await res.json();

        if (json.status === 'success') {
            tbody.innerHTML = json.metrics.map(m => `
                <tr>
                    <td style="font-weight:500;">${m.issue}</td>
                    <td><span class="badge" style="background:rgba(244, 63, 94, 0.15); color:var(--accent-rose);">${m.before}</span></td>
                    <td><span class="badge" style="background:rgba(16, 185, 129, 0.15); color:var(--accent-emerald);">${m.after}</span></td>
                    <td><strong>${m.fixed}</strong></td>
                    <td style="color:var(--text-secondary); font-size:12px;">${m.technique}</td>
                </tr>
            `).join('');
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="color:var(--accent-rose)">Failed to load report</td></tr>`;
    }
}

// ── 6. Visualizations Gallery ──────────────────────────────────────────────

async function loadVisualizationsGallery() {
    const gallery = document.getElementById('viz-gallery');
    try {
        const res = await fetch('/api/visualizations');
        const json = await res.json();

        if (json.status === 'success') {
            gallery.innerHTML = json.charts.map(c => `
                <div class="viz-card" onclick="openModal('${c.title}', '/visualizations/${c.filename}')">
                    <div class="viz-img-wrapper">
                        <img src="/visualizations/${c.filename}" alt="${c.title}" loading="lazy">
                    </div>
                    <div class="viz-card-info">
                        <span class="viz-badge">${c.category}</span>
                        <h4>${c.title}</h4>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) { console.error(e); }
}

function openModal(title, imgUrl) {
    document.getElementById('modal-title').innerText = title;
    document.getElementById('modal-img').src = imgUrl;
    document.getElementById('viz-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('viz-modal').classList.remove('active');
}

// ── 7. Executive Banking Insights ──────────────────────────────────────────

async function loadExecutiveInsights() {
    const container = document.getElementById('insights-container');
    try {
        const res = await fetch('/api/insights');
        const json = await res.json();

        if (json.status === 'success') {
            container.innerHTML = json.insights.map(i => `
                <div class="insight-card">
                    <h3><i class="fa-solid fa-lightbulb" style="color:var(--accent-amber); margin-right:8px;"></i> ${i.title}</h3>
                    <div class="insight-meta">
                        <div class="insight-meta-item">
                            <i class="fa-solid fa-chart-line" style="color:var(--accent-cyan)"></i>
                            <span><strong>Finding:</strong> ${i.metric}</span>
                        </div>
                        <div class="insight-meta-item">
                            <i class="fa-solid fa-shield-cat" style="color:var(--accent-rose)"></i>
                            <span><strong>Business Risk:</strong> ${i.impact}</span>
                        </div>
                    </div>
                    <div class="insight-rec">
                        <i class="fa-solid fa-circle-check" style="color:var(--accent-emerald); margin-right:6px;"></i>
                        <strong>Recommendation:</strong> ${i.recommendation}
                    </div>
                </div>
            `).join('');
        }
    } catch (e) { console.error(e); }
}

// ── 8. Pipeline Execution Console ──────────────────────────────────────────

async function triggerPipeline() {
    const consoleBox = document.getElementById('pipeline-output');
    consoleBox.innerText = "⚡ Triggering main.py pipeline execution...\nGenerating raw data, wrangling, cleaning, building SQLite DB, running analytics & generating charts...\nPlease wait...";

    try {
        const res = await fetch('/api/pipeline/run', { method: 'POST' });
        const json = await res.json();

        if (json.status === 'success') {
            consoleBox.innerText = `✅ PIPELINE COMPLETED SUCCESSFULLY!\n\n${json.stdout}`;
            refreshDashboard();
            loadCleaningAudit();
            loadVisualizationsGallery();
        } else {
            consoleBox.innerText = `❌ PIPELINE EXECUTION FAILED:\n\n${json.stderr || json.message}\n\nSTDOUT:\n${json.stdout}`;
        }
    } catch (err) {
        consoleBox.innerText = `❌ NETWORK ERROR: ${err.message}`;
    }
}
