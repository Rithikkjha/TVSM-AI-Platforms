/**
 * MPCP Project Tracker Frontend Module
 * Renders Dashboard, MP List, CP List, Project Detail (Process Track, Execution Track,
 * Dependencies, Budget), Modals (Create/Edit, RAG Update), and Search.
 */

// ============ MPCP STATE ============
let mpcp = {
    mps: [],
    cps: [],
    projects: [],
    dashboard: null,
    currentMp: null,
    currentCp: null,
    currentProject: null,
    processTrack: null,
    executionTrack: null,
    dependencies: [],
    budget: null,
    buFilter: null, // 'IND-2W', '3W/CMB', 'IB', or null (All)
    filters: {},
};

const MPCP_API = '/api/mpcp-tracker';

function mpHeaders() {
    const h = { 'Authorization': 'Bearer ' + (localStorage.getItem('auth_token') || 'demo-token') };
    return h;
}

function mpHeadersJson() {
    return { ...mpHeaders(), 'Content-Type': 'application/json' };
}

async function downloadMPCPFile(url, filename) {
    try {
        const resp = await fetch(url, { headers: mpHeaders() });
        if (!resp.ok) throw new Error('Download failed');
        const blob = await resp.blob();
        const link = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = link;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(link);
    } catch(e) { showToastNotification(e.message, 'error'); }
}

// ============ MAIN ROUTER ============
async function renderMPCPTracker(hash) {
    const container = document.getElementById('mpcp-container');
    if (!container) return;
    const route = hash.replace('mpcp-tracker', '').replace(/^\//, '');

    if (!route || route === '') {
        await renderMPCPDashboard(container);
    } else if (route === 'projects') {
        await renderAllProjects(container);
    } else if (route === 'mps') {
        await renderMPList(container);
    } else if (route.startsWith('mps/')) {
        const mpId = route.replace('mps/', '');
        await renderCPList(container, mpId);
    } else if (route.startsWith('projects/')) {
        const projectId = route.replace('projects/', '');
        await renderProjectDetail(container, projectId);
    } else if (route.startsWith('cps/') && route.endsWith('/projects')) {
        const cpId = route.replace('cps/', '').replace('/projects', '');
        await renderCPProjects(container, cpId);
    } else if (route === 'settings') {
        await renderMPCPSettings(container);
    } else {
        await renderMPCPDashboard(container);
    }
}

// ============ BU SWITCHER BAR ============
function renderBUSwitcher() {
    const bus = [null, 'IND-2W', '3W/CMB', 'IB'];
    const labels = ['All', 'IND-2W', '3W/CMB', 'IB'];
    // Get current FY label (Apr-Mar)
    const now = new Date();
    const fyStart = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1;
    const fyEnd = (fyStart + 1) % 100;
    const currentFyValue = `${fyStart}_${fyEnd < 10 ? '0' + fyEnd : fyEnd}`;
    const activeFy = mpcp.activeFy || currentFyValue;
    const availableFys = [
        { value: '2026_27', label: 'FY 2026-27' },
        { value: '2025_26', label: 'FY 2025-26' },
        { value: '2024_25', label: 'FY 2024-25' },
    ];
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div class="bu-switcher" style="display:flex;gap:4px;">
            ${bus.map((bu, i) => `<button class="btn btn-sm ${mpcp.buFilter === bu ? 'btn-primary' : 'btn-secondary'}"
                onclick="mpcp.buFilter=${bu ? "'" + bu + "'" : 'null'};renderMPCPTracker(window.location.hash.slice(1))">${labels[i]}</button>`).join('')}
        </div>
        <select id="mpcp-fy-select" style="font-size:12px;font-weight:600;color:#1a237e;background:#e8eaf6;border:1px solid #c5cae9;padding:4px 8px;border-radius:6px;cursor:pointer" onchange="switchFY(this.value)">
            ${availableFys.map(fy => `<option value="${fy.value}" ${fy.value === activeFy ? 'selected' : ''}>${fy.label}</option>`).join('')}
        </select>
    </div>`;
}

async function switchFY(fyLabel) {
    try {
        const resp = await fetch(`${MPCP_API}/fy/${fyLabel}`, { method: 'POST', headers: mpHeaders() });
        if (!resp.ok) throw new Error('Failed to switch FY');
        mpcp.activeFy = fyLabel;
        showToastNotification(`Switched to FY ${fyLabel.replace('_', '-')}`, 'success');
        renderMPCPTracker(window.location.hash.slice(1));
    } catch (e) {
        showToastNotification(e.message, 'error');
    }
}

// ============ DASHBOARD ============
async function renderMPCPDashboard(container) {
    container.innerHTML = '<div class="card"><p>Loading dashboard...</p></div>';
    try {
        const params = new URLSearchParams();
        if (mpcp.buFilter) params.set('bu', mpcp.buFilter);
        const resp = await fetch(`${MPCP_API}/dashboard?${params}`, { headers: mpHeaders() });
        if (!resp.ok) {
            const errText = await resp.text();
            throw new Error(`HTTP ${resp.status}: ${errText}`);
        }
        mpcp.dashboard = await resp.json();
    } catch (e) {
        container.innerHTML = `<div class="card"><p style="color:#c62828">Error: ${e.message}</p></div>`;
        return;
    }
    const d = mpcp.dashboard;
    container.innerHTML = `
        ${renderBUSwitcher()}
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <div></div>
            <div style="display:flex;gap:8px">
                <button class="btn btn-secondary btn-sm" onclick="downloadMPCPFile('${MPCP_API}/export','MPCP_Report.xlsx')">📥 Download Report</button>
                <button class="btn btn-secondary btn-sm" onclick="downloadMPCPFile('${MPCP_API}/export/3w1h','3W1H_Report.xlsx')">📥 3W1H Report</button>
                <button class="btn btn-secondary btn-sm" onclick="sendWeeklyReport()">📧 Send Weekly Report</button>
            </div>
        </div>
        <div class="metrics-grid">
            <div class="metric-card"><h4>Total Projects</h4><div class="value">${d.total_projects}</div></div>
            <div class="metric-card green"><h4>Green</h4><div class="value">${d.green_count}</div></div>
            <div class="metric-card yellow"><h4>Yellow</h4><div class="value">${d.yellow_count}</div></div>
            <div class="metric-card red"><h4>Red</h4><div class="value">${d.red_count}</div></div>
            <div class="metric-card deps"><h4>Open Deps</h4><div class="value">${d.open_dependencies}</div></div>
            <div class="metric-card"><h4>Budget Approved</h4><div class="value">₹${fmt(d.budget_total_approved)}</div></div>
            <div class="metric-card"><h4>Budget Remaining</h4><div class="value">₹${fmt(d.budget_total_remaining)}</div></div>
            <div class="metric-card ${d.budget_over_count > 0 ? 'red' : ''}"><h4>Over Budget</h4><div class="value">${d.budget_over_count}</div></div>
        </div>
        <div class="card">
            <h3>By Vendor</h3>
            <table class="data-table"><thead><tr><th>Vendor</th><th>Total</th><th>Green</th><th>Yellow</th><th>Red</th></tr></thead><tbody>
            ${Object.entries(d.by_vendor).map(([v, c]) => `<tr><td>${v}</td><td>${c.total}</td><td><span class="rag-badge green">${c.Green}</span></td><td><span class="rag-badge yellow">${c.Yellow}</span></td><td><span class="rag-badge red">${c.Red}</span></td></tr>`).join('')}
            </tbody></table>
        </div>
        <div class="card">
            <h3>By Product Owner</h3>
            <table class="data-table"><thead><tr><th>PO</th><th>Total</th><th>Green</th><th>Yellow</th><th>Red</th></tr></thead><tbody>
            ${Object.entries(d.by_po).map(([po, c]) => `<tr><td>${po}</td><td>${c.total}</td><td><span class="rag-badge green">${c.Green}</span></td><td><span class="rag-badge yellow">${c.Yellow}</span></td><td><span class="rag-badge red">${c.Red}</span></td></tr>`).join('')}
            </tbody></table>
        </div>
        ${d.critical_items.length > 0 ? `<div class="card">
            <h3 style="color:#c62828">🔴 Critical Items (Red)</h3>
            <table class="data-table"><thead><tr><th>Project</th><th>Vendor</th><th>Why</th><th>Owner</th><th>ETA</th></tr></thead><tbody>
            ${d.critical_items.map(c => `<tr><td>${c.project_name}</td><td>${c.vendor}</td><td>${c.why || '-'}</td><td>${c.who || '-'}</td><td>${c.eta || '-'}</td></tr>`).join('')}
            </tbody></table>
        </div>` : ''}
        ${d.open_dependencies_list.length > 0 ? `<div class="card">
            <h3 style="color:#e65100">⚠️ Open Dependencies</h3>
            <table class="data-table"><thead><tr><th>Description</th><th>Owner</th><th>Cutoff</th><th>Days Overdue</th><th>Status</th></tr></thead><tbody>
            ${d.open_dependencies_list.map(dep => `<tr class="${dep.days_overdue > 0 ? 'overdue' : ''}"><td>${dep.description}</td><td>${dep.external_owner}</td><td>${dep.cutoff_date}</td><td>${dep.days_overdue > 0 ? '<span style="color:#c62828;font-weight:600">'+dep.days_overdue+'</span>' : '0'}</td><td>${dep.status}</td></tr>`).join('')}
            </tbody></table>
        </div>` : ''}
    `;
}

// ============ MP LIST ============
async function renderMPList(container) {
    container.innerHTML = '<div class="card"><p>Loading Managing Points...</p></div>';
    try {
        const resp = await fetch(`${MPCP_API}/mps`, { headers: mpHeaders() });
        if (!resp.ok) throw new Error('Failed to load MPs');
        mpcp.mps = await resp.json();
    } catch (e) {
        container.innerHTML = `<div class="card"><p style="color:#c62828">Error: ${e.message}</p></div>`;
        return;
    }
    container.innerHTML = `
        ${renderBUSwitcher()}
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h2>📈 Managing Points</h2>
                <div style="display:flex;gap:8px">
                    <button class="btn btn-secondary btn-sm" onclick="downloadHierarchyTemplate()">📥 Download Template</button>
                    <button class="btn btn-secondary btn-sm" onclick="document.getElementById('bulk-upload-input').click()">📤 Bulk Upload</button>
                    <input type="file" id="bulk-upload-input" accept=".xlsx,.xls" style="display:none" onchange="handleBulkUpload(this)">
                    <button class="btn btn-primary btn-sm" onclick="showCreateMPModal()">+ Add MP</button>
                </div>
            </div>
            <table class="data-table"><thead><tr><th>Code</th><th>Theme</th><th>Name</th><th>Owner</th><th>BU</th><th>RAG</th><th>CPs</th><th>Projects</th><th></th></tr></thead><tbody>
            ${mpcp.mps.filter(mp => !mpcp.buFilter || mp.bu === mpcp.buFilter).map(mp => `<tr style="cursor:pointer" onclick="navigateTo('#mpcp-tracker/mps/${mp.id}')">
                <td><strong>${mp.code}</strong></td><td>${{A:'Customer Satisfaction',B:'Profit & Profitability',C:'Business Growth',D:'New Product Development',E:'Effectiveness of People & System',F:'Digitalization & AI',Z:'Others (Non-MPCP)'}[mp.theme] || mp.theme}</td><td>${mp.name}</td><td>${mp.owner}</td><td>${mp.bu}</td>
                <td><span class="rag-badge ${(mp.propagated_rag || mp.rag_status).toLowerCase()}">${mp.propagated_rag || mp.rag_status}</span></td>
                <td>${mp.cp_count}</td><td>${mp.project_count}</td>
                <td><button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();showEditMPModal('${mp.id}')">✏️</button></td>
            </tr>`).join('')}
            ${mpcp.mps.filter(mp => !mpcp.buFilter || mp.bu === mpcp.buFilter).length === 0 ? '<tr><td colspan="9" style="text-align:center;color:#999">No Managing Points for this BU.</td></tr>' : ''}
            </tbody></table>
        </div>
    `;
}

// ============ CP LIST ============
async function renderCPList(container, mpId) {
    container.innerHTML = '<div class="card"><p>Loading Check Points...</p></div>';
    try {
        const [mpResp, cpsResp] = await Promise.all([
            fetch(`${MPCP_API}/mps/${mpId}`, { headers: mpHeaders() }),
            fetch(`${MPCP_API}/mps/${mpId}/cps`, { headers: mpHeaders() }),
        ]);
        if (!mpResp.ok || !cpsResp.ok) throw new Error('Failed to load');
        mpcp.currentMp = await mpResp.json();
        mpcp.cps = await cpsResp.json();
    } catch (e) {
        container.innerHTML = `<div class="card"><p style="color:#c62828">Error: ${e.message}</p></div>`;
        return;
    }
    const mp = mpcp.currentMp;
    container.innerHTML = `
        <div class="breadcrumb"><a onclick="navigateTo('#mpcp-tracker/mps')">MPs</a> <span class="sep">›</span> <strong>${mp.code} - ${mp.name}</strong></div>
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h2>Check Points under ${mp.code}</h2>
                <button class="btn btn-primary btn-sm" onclick="showCreateCPModal('${mpId}')">+ Add CP</button>
            </div>
            <table class="data-table"><thead><tr><th>Code</th><th>Name</th><th>Owner</th><th>Domain</th><th>Stream</th><th>RAG</th><th>Projects</th><th></th></tr></thead><tbody>
            ${mpcp.cps.map(cp => `<tr style="cursor:pointer" onclick="navigateTo('#mpcp-tracker/cps/${cp.id}/projects')">
                <td><strong>${cp.code}</strong></td><td>${cp.name}</td><td>${cp.owner}</td><td>${cp.domain || '-'}</td><td>${cp.stream || '-'}</td>
                <td><span class="rag-badge ${(cp.propagated_rag || cp.rag_status).toLowerCase()}">${cp.propagated_rag || cp.rag_status}</span></td>
                <td>${cp.project_count}</td>
                <td><button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();showEditCPModal('${cp.id}')">✏️</button></td>
            </tr>`).join('')}
            ${mpcp.cps.length === 0 ? '<tr><td colspan="8" style="text-align:center;color:#999">No Check Points yet.</td></tr>' : ''}
            </tbody></table>
        </div>
    `;
}

// ============ CP PROJECTS LIST ============
async function renderCPProjects(container, cpId) {
    container.innerHTML = '<div class="card"><p>Loading projects...</p></div>';
    try {
        const [cpResp, projResp] = await Promise.all([
            fetch(`${MPCP_API}/cps/${cpId}`, { headers: mpHeaders() }),
            fetch(`${MPCP_API}/cps/${cpId}/projects`, { headers: mpHeaders() }),
        ]);
        if (!cpResp.ok || !projResp.ok) throw new Error('Failed to load');
        const cp = await cpResp.json();
        const projects = await projResp.json();

        // Get parent MP info for breadcrumb
        let mpCode = '';
        let mpId = cp.parent_mp_id;
        if (mpId) {
            try {
                const mpResp = await fetch(`${MPCP_API}/mps/${mpId}`, { headers: mpHeaders() });
                if (mpResp.ok) {
                    const mp = await mpResp.json();
                    mpCode = mp.code;
                }
            } catch (e) { /* ignore */ }
        }

        container.innerHTML = `
            <div class="breadcrumb">
                <a onclick="navigateTo('#mpcp-tracker/mps')">MPs</a> <span class="sep">›</span> 
                <a onclick="navigateTo('#mpcp-tracker/mps/${mpId}')">${mpCode}</a> <span class="sep">›</span> 
                <strong>${cp.code}</strong> <span class="sep">›</span> 
                <span>Projects</span>
            </div>
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                    <h2>Projects under ${cp.code} - ${cp.name}</h2>
                    <button class="btn btn-primary btn-sm" onclick="showCreateProjectModal('${cpId}')">+ Add Project</button>
                </div>
                <table class="data-table"><thead><tr><th>Name</th><th>Type</th><th>Vendor</th><th>Product Owner</th><th>RAG</th><th>Stage</th></tr></thead><tbody>
                ${projects.map(p => `<tr style="cursor:pointer" onclick="navigateTo('#mpcp-tracker/projects/${p.id}')">
                    <td><strong>${p.name}</strong></td>
                    <td>${p.project_type || '-'}</td>
                    <td>${p.vendor || '-'}</td>
                    <td>${p.product_owner || '-'}</td>
                    <td><span class="rag-badge ${(p.rag_status || 'green').toLowerCase()}">${p.rag_status || 'Green'}</span></td>
                    <td>${p.current_stage || '-'}</td>
                </tr>`).join('')}
                ${projects.length === 0 ? '<tr><td colspan="6" style="text-align:center;color:#999">No projects yet. Click "+ Add Project" to create one.</td></tr>' : ''}
                </tbody></table>
            </div>
        `;
    } catch (e) {
        container.innerHTML = `<div class="card"><p style="color:#c62828">Error: ${e.message}</p></div>`;
    }
}

// ============ ALL PROJECTS ============
async function renderAllProjects(container) {
    container.innerHTML = '<div class="card"><p>Loading projects...</p></div>';
    try {
        const [projResp, mpsResp, cpsResp] = await Promise.all([
            fetch(`${MPCP_API}/projects/all`, { headers: mpHeaders() }),
            fetch(`${MPCP_API}/mps`, { headers: mpHeaders() }),
            fetch(`${MPCP_API}/cps/all`, { headers: mpHeaders() }),
        ]);
        if (!projResp.ok) throw new Error('Failed to load projects');
        mpcp.projects = await projResp.json();
        const allMps = mpsResp.ok ? await mpsResp.json() : [];
        const allCps = cpsResp.ok ? await cpsResp.json() : [];

        // Build MP lookup for enriching CPs
        const mpLookup = {};
        allMps.forEach(mp => { mpLookup[mp.id] = mp; });
        allCps.forEach(cp => {
            const mp = mpLookup[cp.parent_mp_id];
            cp._mp_code = mp ? mp.code : '';
            cp._mp_name = mp ? mp.name : '';
        });

        // Build lookup: cp_id → {cp_code, mp_code}
        window._cpLookup = {};
        allCps.forEach(cp => { window._cpLookup[cp.id] = { cp_code: cp.code, cp_name: cp.name, mp_code: cp._mp_code }; });
    } catch (e) {
        container.innerHTML = `<div class="card"><p style="color:#c62828">Error: ${e.message}</p></div>`;
        return;
    }
    container.innerHTML = `
        ${renderBUSwitcher()}
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h2>All Projects</h2>
                <button class="btn btn-primary btn-sm" onclick="showCreateProjectPickerModal()">+ Add Project</button>
            </div>
            <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;">
                <input type="text" id="mpcp-search" placeholder="Search by name..." style="padding:6px 12px;border:1px solid #ddd;border-radius:6px;font-size:12px;width:200px" oninput="filterProjectList()">
                <select id="mpcp-rag-filter" style="padding:6px;border:1px solid #ddd;border-radius:6px;font-size:12px" onchange="filterProjectList()">
                    <option value="">All RAG</option><option value="Green">Green</option><option value="Yellow">Yellow</option><option value="Red">Red</option>
                </select>
                <select id="mpcp-vendor-filter" style="padding:6px;border:1px solid #ddd;border-radius:6px;font-size:12px" onchange="filterProjectList()">
                    <option value="">All Vendors</option><option>Exathought</option><option>Deloitte</option><option>TVSD</option><option>Evontech</option><option>Autovyn</option>
                </select>
            </div>
            <div class="table-scroll">
            <table class="data-table" id="mpcp-projects-table"><thead><tr><th>MP / CP</th><th>Name</th><th>Type</th><th>Vendor</th><th>PO</th><th>RAG</th><th>Stage</th></tr></thead><tbody>
            ${renderProjectRows(mpcp.projects)}
            </tbody></table>
            </div>
        </div>
    `;
}

function renderProjectRows(projects) {
    // Apply BU filter
    let filtered = projects;
    if (mpcp.buFilter) {
        filtered = projects.filter(p => p.bu === mpcp.buFilter);
    }
    if (!filtered.length) return '<tr><td colspan="7" style="text-align:center;color:#999">No projects found for this BU.</td></tr>';
    const lookup = window._cpLookup || {};
    return filtered.map(p => {
        const cpInfo = lookup[p.parent_cp_id] || {};
        const hierarchy = cpInfo.mp_code ? `${cpInfo.mp_code} › ${cpInfo.cp_code}` : (cpInfo.cp_code || '-');
        return `<tr onclick="navigateTo('#mpcp-tracker/projects/${p.id}')" style="cursor:pointer">
        <td><span style="font-size:11px;color:#1a237e;font-weight:500">${hierarchy}</span></td>
        <td><strong>${p.name}</strong></td><td><span class="badge" style="background:#e3f2fd;color:#1565c0">${p.project_type || '-'}</span></td>
        <td>${p.vendor || '-'}</td><td>${p.product_owner || '-'}</td>
        <td><span class="rag-badge ${(p.rag_status || 'green').toLowerCase()}">${p.rag_status || 'Green'}</span></td>
        <td>${p.current_stage || '-'}</td>
    </tr>`;
    }).join('');
}

function filterProjectList() {
    const q = (document.getElementById('mpcp-search')?.value || '').toLowerCase();
    const rag = document.getElementById('mpcp-rag-filter')?.value || '';
    const vendor = document.getElementById('mpcp-vendor-filter')?.value || '';
    let filtered = mpcp.projects;
    if (q) filtered = filtered.filter(p => p.name.toLowerCase().includes(q));
    if (rag) filtered = filtered.filter(p => p.rag_status === rag);
    if (vendor) filtered = filtered.filter(p => p.vendor === vendor);
    const tbody = document.querySelector('#mpcp-projects-table tbody');
    if (tbody) tbody.innerHTML = renderProjectRows(filtered);
}

// ============ PROJECT DETAIL ============
async function renderProjectDetail(container, projectId) {
    container.innerHTML = '<div class="card"><p>Loading project...</p></div>';
    try {
        const [projResp, ptResp, etResp, depResp, budResp] = await Promise.all([
            fetch(`${MPCP_API}/projects/${projectId}`, { headers: mpHeaders() }),
            fetch(`${MPCP_API}/projects/${projectId}/process-track`, { headers: mpHeaders() }),
            fetch(`${MPCP_API}/projects/${projectId}/execution-track`, { headers: mpHeaders() }),
            fetch(`${MPCP_API}/projects/${projectId}/dependencies`, { headers: mpHeaders() }),
            fetch(`${MPCP_API}/projects/${projectId}/budget`, { headers: mpHeaders() }),
        ]);
        if (!projResp.ok) throw new Error('Project not found');
        mpcp.currentProject = await projResp.json();
        mpcp.currentProjectId = projectId;
        mpcp.processTrack = ptResp.ok ? await ptResp.json() : null;
        mpcp.executionTrack = etResp.ok ? await etResp.json() : null;
        mpcp.dependencies = depResp.ok ? await depResp.json() : [];
        mpcp.budget = budResp.ok ? await budResp.json() : null;
        // Load all tasks for Gantt chart rendering
        await loadGanttTasks(projectId);
    } catch (e) {
        container.innerHTML = `<div class="card"><p style="color:#c62828">Error: ${e.message}</p></div>`;
        return;
    }
    const p = mpcp.currentProject;
    container.innerHTML = `
        <div class="breadcrumb"><a onclick="navigateTo('#mpcp-tracker/mps')">MPs</a>  <span class="sep">›</span>  <a onclick="navigateTo('#mpcp-tracker/projects')">Projects</a>  <span class="sep">›</span>  <strong>${p.name}</strong></div>
        <div class="card" style="margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
                <div>
                    <h2>${p.name}</h2>
                    <p style="font-size:12px;color:#666;margin-top:4px">
                        ${p.bu ? `<span style="background:#e8eaf6;color:#1a237e;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">${p.bu}</span>` : ''}
                        ${p.domain ? `<span style="background:#e3f2fd;color:#1565c0;padding:2px 8px;border-radius:10px;font-size:11px">${p.domain}</span>` : ''}
                        ${p.stream ? `<span style="background:#f3e5f5;color:#7b1fa2;padding:2px 8px;border-radius:10px;font-size:11px">${p.stream}</span>` : ''}
                        ${p.vendor ? ` · Vendor: <strong>${p.vendor}</strong>` : ''}
                        ${p.product_owner ? ` · PO: ${p.product_owner}` : ''}
                        ${p.engg_poc ? ` · Engg: <strong>${p.engg_poc}</strong>` : ''}
                        ${p.project_type ? ` · Type: ${p.project_type}` : ''}
                    </p>
                </div>
                <div style="display:flex;gap:8px;align-items:center">
                    <span class="rag-badge ${p.rag_status.toLowerCase()}" style="font-size:13px;padding:4px 12px">${p.rag_status}</span>
                    ${(() => {
                        const b = mpcp.budget;
                        if (!b || !b.approved_budget) return '';
                        const pct = Math.round(b.total_committed / b.approved_budget * 100);
                        const color = pct > 100 ? '#c62828' : pct > 80 ? '#e65100' : '#2e7d32';
                        const label = pct > 100 ? 'Over Budget' : pct > 80 ? 'At Risk' : 'On Track';
                        const icon = pct > 100 ? '🔴' : pct > 80 ? '🟡' : '🟢';
                        return `<span style="font-size:11px;padding:4px 10px;border-radius:10px;background:${pct > 100 ? '#ffebee' : pct > 80 ? '#fff3e0' : '#e8f5e9'};color:${color};font-weight:600">${icon} ₹${b.total_committed}/${b.approved_budget} (${pct}%) — ${label}</span>`;
                    })()}
                    <button class="btn btn-sm btn-secondary" onclick="showEditProjectModal('${p.id}')">✏️ Edit</button>
                    <button class="btn btn-sm btn-secondary" onclick="showMoveProjectModal('${p.id}')">↔️ Move</button>
                    <button class="btn btn-sm btn-secondary" onclick="showRAGModal('Project','${p.id}','${p.rag_status}')">Update RAG</button>
                </div>
            </div>
        </div>
        <div class="tab-bar" id="mpcp-detail-tabs">
            <div class="tab-item active" onclick="showMPCPTab('process')">Process Track</div>
            <div class="tab-item" onclick="showMPCPTab('execution')">Execution Track</div>
            <div class="tab-item" onclick="showMPCPTab('dependencies')">Dependencies (${mpcp.dependencies.length})</div>
            <div class="tab-item" onclick="showMPCPTab('budget')">Budget</div>
            <div class="tab-item" onclick="showMPCPTab('changelog');loadChangeLogData()">Change Log</div>
        </div>
        <div id="mpcp-tab-process" class="mpcp-tab-content">${renderProcessTrack()}</div>
        <div id="mpcp-tab-execution" class="mpcp-tab-content" style="display:none">${renderExecutionTrack(projectId)}</div>
        <div id="mpcp-tab-dependencies" class="mpcp-tab-content" style="display:none">${renderDependenciesTab(projectId)}</div>
        <div id="mpcp-tab-budget" class="mpcp-tab-content" style="display:none">${renderBudgetTab(projectId)}</div>
        <div id="mpcp-tab-changelog" class="mpcp-tab-content" style="display:none">${renderChangeLogTab(projectId)}</div>
    `;
}

function showMPCPTab(tab) {
    document.querySelectorAll('.mpcp-tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('#mpcp-detail-tabs .tab-item').forEach(el => el.classList.remove('active'));
    document.getElementById('mpcp-tab-' + tab).style.display = 'block';
    // Mark clicked tab as active
    const tabMap = { 'process': 'process', 'execution': 'execution', 'dependencies': 'dependencies', 'budget': 'budget', 'changelog': 'change' };
    const matchPrefix = tabMap[tab] || tab;
    document.querySelectorAll('#mpcp-detail-tabs .tab-item').forEach(el => {
        if (el.textContent.toLowerCase().startsWith(matchPrefix)) el.classList.add('active');
    });
    // Lazy-load changelog when tab is clicked
    if (tab === 'changelog') loadChangeLogData();
}

// ============ PROCESS TRACK TAB ============
function renderProcessTrack() {
    if (!mpcp.processTrack || !mpcp.processTrack.stages) return '<div class="card"><p>No process track data.</p></div>';
    const stages = mpcp.processTrack.stages;
    const stageIcons = { 'Completed': '●', 'In_Progress': '◐', 'Not_Started': '○', 'Skipped': '⊘' };
    const stageColors = { 'Completed': '#4caf50', 'In_Progress': '#2196f3', 'Not_Started': '#ccc', 'Skipped': '#999' };

    let stepper = '<div style="display:flex;align-items:center;gap:0;margin-bottom:24px;overflow-x:auto;padding:12px 0">';
    stages.forEach((s, i) => {
        const color = stageColors[s.status];
        const canAdvance = i === 0 || stages.slice(0, i).every(prev => prev.status === 'Completed' || prev.status === 'Skipped');
        const clickAttr = canAdvance ? `onclick="showStageEditModal('${s.project_id}','${s.stage}',${s.stage_order})"` : '';
        const cursor = canAdvance ? 'cursor:pointer' : 'cursor:not-allowed;opacity:0.5';
        const hoverStyle = canAdvance ? 'transition:transform 0.2s;' : '';
        const updateLabel = canAdvance && s.status !== 'Completed' ? `<div style="font-size:9px;color:#1a237e;font-weight:600;margin-top:2px">▶ Update</div>` : '';
        stepper += `<div style="display:flex;flex-direction:column;align-items:center;min-width:80px;${cursor};${hoverStyle}" ${clickAttr}
            onmouseover="if(${canAdvance})this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
            <div style="width:40px;height:40px;border-radius:50%;background:${color};display:flex;align-items:center;justify-content:center;color:white;font-size:16px;font-weight:bold;${canAdvance?'box-shadow:0 2px 8px rgba(0,0,0,0.2)':''}">${stageIcons[s.status]}</div>
            <div style="font-size:10px;margin-top:4px;color:#333;font-weight:600">${s.stage}</div>
            <div style="font-size:9px;color:#999">${s.actual_date || s.planned_date || ''}</div>
            ${updateLabel}
        </div>`;
        if (i < stages.length - 1) {
            const connColor = stages[i].status === 'Completed' || stages[i].status === 'Skipped' ? '#4caf50' : '#e0e0e0';
            stepper += `<div style="flex:1;height:3px;background:${connColor};min-width:20px"></div>`;
        }
    });
    stepper += '</div>';

    return `<div class="card">
        <h3>Process Track</h3>
        <p class="subtitle">Click a stage circle to update status • Click dates to edit inline</p>
        ${stepper}
        <table class="data-table"><thead><tr><th>Stage</th><th>Status</th><th>Planned Date</th><th>Actual Date</th><th>Delay (days)</th><th>Remarks</th></tr></thead><tbody>
        ${stages.map(s => {
            let delay = '';
            let delayStyle = '';
            if (s.planned_date && s.actual_date) {
                const d = Math.round((new Date(s.actual_date) - new Date(s.planned_date)) / 86400000);
                if (d > 0) { delay = '+' + d + 'd'; delayStyle = 'color:#fff;background:#c62828;padding:2px 6px;border-radius:4px;font-weight:600;font-size:11px'; }
                else if (d === 0) { delay = '0d'; delayStyle = 'color:#2e7d32;font-weight:600'; }
                else { delay = d + 'd'; delayStyle = 'color:#2e7d32;font-weight:600'; }
            } else if (s.planned_date && !s.actual_date && s.status !== 'Completed' && s.status !== 'Skipped') {
                const today = new Date(); today.setHours(0,0,0,0);
                const planned = new Date(s.planned_date);
                if (today > planned) { const d = Math.round((today - planned) / 86400000); delay = '+' + d + 'd overdue'; delayStyle = 'color:#fff;background:#c62828;padding:2px 6px;border-radius:4px;font-weight:600;font-size:11px'; }
            }
            const plannedDisplay = s.planned_date || '';
            const actualDisplay = s.actual_date || '';
            const canEditActual = s.status === 'In_Progress' || s.status === 'Completed';
            return `<tr>
                <td><strong>${s.stage}</strong></td>
                <td><span class="rag-badge ${s.status === 'Completed' ? 'green' : s.status === 'In_Progress' ? 'yellow' : ''}">${s.status}</span></td>
                <td class="inline-date-cell" onclick="inlineDateEdit(this,'${s.project_id}','${s.stage}','planned_date','${plannedDisplay}')" style="cursor:pointer;color:#1565c0;font-weight:500;position:relative" title="Click to set planned date">
                    <span class="date-display">${plannedDisplay || '<span style="color:#bbb;font-weight:400">+ Set date</span>'}</span>
                </td>
                ${canEditActual ? `<td class="inline-date-cell" onclick="inlineDateEdit(this,'${s.project_id}','${s.stage}','actual_date','${actualDisplay}')" style="cursor:pointer;font-weight:600;position:relative;${actualDisplay && s.planned_date && new Date(actualDisplay) > new Date(s.planned_date) ? 'color:#c62828' : 'color:#2e7d32'}" title="Click to set actual date">
                    <span class="date-display">${actualDisplay || '<span style="color:#bbb;font-weight:400">+ Set date</span>'}</span>
                </td>` : `<td style="font-weight:600;color:#999">${actualDisplay || '-'}</td>`}
                <td><span style="${delayStyle}">${delay || '-'}</span></td>
                <td>${s.remarks || s.skip_reason || '-'}</td>
            </tr>`;
        }).join('')}
        </tbody></table>
    </div>`;
}

// ============ EXECUTION TRACK TAB ============
function renderExecutionTrack(projectId) {
    const et = mpcp.executionTrack;
    if (!et) return '<div class="card"><p>No execution track data.</p></div>';
    const ms = et.milestones || [];

    // Check for project-level blockers
    const allBlockers = mpcp.dependencies.filter(d => d.is_blocker && d.status !== 'Resolved');
    let blockerBanner = '';
    if (allBlockers.length > 0) {
        blockerBanner = `<div style="background:#ffebee;border:1px solid #ef9a9a;border-left:4px solid #c62828;border-radius:8px;padding:12px 16px;margin-bottom:14px;">
            <div style="font-weight:700;color:#c62828;font-size:13px;margin-bottom:6px">🚫 ${allBlockers.length} Active Blocker${allBlockers.length>1?'s':''}</div>
            ${allBlockers.map(d => `<div style="font-size:12px;color:#333;margin-bottom:4px">• <strong>${d.description}</strong> <span style="color:#666">(Owner: ${d.external_owner}, ETA: ${d.cutoff_date})</span>${d.is_overdue ? ' <span style="color:#c62828;font-weight:600">⚠️ OVERDUE</span>' : ''}</div>`).join('')}
        </div>`;
    }

    // Build milestone sections (expandable)
    let milestonesHtml = '';
    ms.forEach((m, idx) => {
        const delayLabel = (m.slippage_days != null && m.slippage_days !== 0)
            ? `<span style="color:${m.slippage_days > 0 ? '#c62828' : '#2e7d32'};font-weight:600">${m.slippage_days > 0 ? '+' : ''}${m.slippage_days}d</span>`
            : '<span style="color:#999">-</span>';
        const plannedRange = (m.planned_start && m.planned_end) ? `${m.planned_start} → ${m.planned_end}` : 'Not set';
        const actualRange = (m.actual_start || m.actual_end) ? `${m.actual_start || '?'} → ${m.actual_end || '?'}` : '-';

        // Check for open dependencies linked to this milestone
        const linkedDeps = mpcp.dependencies.filter(d => d.milestone_id === m.id && d.status !== 'Resolved');
        const overdueDeps = linkedDeps.filter(d => d.is_overdue);
        const blockerDeps = linkedDeps.filter(d => d.is_blocker);
        let depBadge = '';
        if (blockerDeps.length > 0) {
            depBadge = `<span onclick="event.stopPropagation();showMPCPTab('dependencies')" title="${blockerDeps.map(d=>d.description).join(', ')}" style="cursor:pointer;background:#c62828;color:white;padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;animation:pulse 2s infinite">🚫 ${blockerDeps.length} BLOCKER${blockerDeps.length>1?'S':''}</span>`;
            if (overdueDeps.length > 0) depBadge += ` <span style="background:#ffebee;color:#c62828;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600">${overdueDeps.length} overdue</span>`;
        } else if (overdueDeps.length > 0) {
            depBadge = `<span onclick="event.stopPropagation();showMPCPTab('dependencies')" title="Click to view dependencies" style="cursor:pointer;background:#ffebee;color:#c62828;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600">🔗 ${linkedDeps.length} dep (${overdueDeps.length} overdue)</span>`;
        } else if (linkedDeps.length > 0) {
            depBadge = `<span onclick="event.stopPropagation();showMPCPTab('dependencies')" title="Click to view dependencies" style="cursor:pointer;background:#e3f2fd;color:#1565c0;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600">🔗 ${linkedDeps.length} dep</span>`;
        }

        milestonesHtml += `
        <div class="milestone-section" style="border:1px solid #e0e0e0;border-radius:8px;margin-bottom:10px;overflow:hidden">
            <div class="milestone-header" onclick="toggleMilestoneSection('ms-${idx}')" style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#f5f7fa;cursor:pointer;user-select:none">
                <div style="display:flex;align-items:center;gap:10px">
                    <span id="ms-chevron-${idx}" style="transition:transform 0.2s;font-size:12px">▶</span>
                    <strong style="font-size:13px">${idx + 1}. ${m.name}</strong>
                    ${m.vendor ? `<span style="font-size:11px;color:#666;background:#e8eaf6;padding:2px 8px;border-radius:4px">${m.vendor}</span>` : ''}
                    ${depBadge}
                </div>
                <div style="display:flex;align-items:center;gap:8px;font-size:11px">
                    <span style="color:#666">Planned: ${plannedRange}</span>
                    <span style="color:#666">|</span>
                    <span style="color:#666">Actual: ${actualRange}</span>
                    <span style="color:#666">|</span>
                    <span>Delay: ${delayLabel}</span>
                    <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();showEditMilestoneModal('${projectId}',${idx})">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="event.stopPropagation();deleteMilestoneConfirm('${projectId}','${m.id}')">🗑️</button>
                    <button class="btn btn-sm btn-primary" onclick="event.stopPropagation();showAddTaskModal('${projectId}','${m.id}')" title="Add Task">+ Task</button>
                </div>
            </div>
            <div id="ms-body-${idx}" style="display:none;padding:12px 16px;background:#fff">
                <div id="ms-tasks-${m.id}" style="font-size:12px;color:#999">Loading tasks...</div>
            </div>
        </div>`;
    });

    return `<div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3>Execution Track</h3>
            <div style="display:flex;gap:8px">
                <button class="btn btn-secondary btn-sm" onclick="downloadMPCPFile('${MPCP_API}/projects/'+mpcp.currentProjectId+'/execution-track/export','Execution_Plan.xlsx')">📥 Download Plan</button>
                <button class="btn btn-primary btn-sm" onclick="showAddMilestoneModal('${projectId}')">+ Add Milestone</button>
            </div>
        </div>
        ${renderGanttChart(ms)}
        ${blockerBanner}
        <div style="display:flex;gap:16px;margin-bottom:12px;font-size:12px">
            <span>📅 Planned: <strong>${et.total_planned_days}d</strong></span>
            <span>✅ Actual: <strong>${et.total_actual_days}d</strong></span>
            <span style="color:${et.cumulative_slippage > 0 ? '#c62828' : '#2e7d32'}">📊 Slippage: <strong>${et.cumulative_slippage}d</strong></span>
            ${et.fast_track_days ? `<span style="color:#2e7d32">🚀 Fast-track: <strong>${et.fast_track_days}d recovered</strong></span>` : ''}
        </div>
        ${milestonesHtml}
    </div>`;
}

function toggleMilestoneSection(sectionId) {
    const idx = sectionId.replace('ms-', '');
    const body = document.getElementById('ms-body-' + idx);
    const chevron = document.getElementById('ms-chevron-' + idx);
    if (body.style.display === 'none') {
        body.style.display = 'block';
        chevron.style.transform = 'rotate(90deg)';
        // Load tasks for this milestone
        const et = mpcp.executionTrack;
        if (et && et.milestones && et.milestones[idx]) {
            const m = et.milestones[idx];
            loadMilestoneTasks(mpcp.currentProjectId, m.id);
        }
    } else {
        body.style.display = 'none';
        chevron.style.transform = 'rotate(0deg)';
    }
}

async function loadMilestoneTasks(projectId, milestoneId) {
    const container = document.getElementById('ms-tasks-' + milestoneId);
    if (!container) return;
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/milestones/${milestoneId}/tasks`, { headers: mpHeaders() });
        if (!resp.ok) throw new Error('Failed to load tasks');
        const tasks = await resp.json();
        _loadedTasks[milestoneId] = tasks; // cache for edit
        if (tasks.length === 0) {
            container.innerHTML = '<p style="color:#999;font-size:12px;margin:4px 0">No tasks yet. Click "+ Task" to add one.</p>';
            return;
        }
        let html = `<table class="data-table" style="font-size:12px"><thead><tr>
            <th>Task</th><th>Owner</th><th>Planned Start</th><th>Planned End</th>
            <th>Actual Start</th><th>Actual End</th><th>Delay</th><th>Remarks</th><th>Actions</th>
        </tr></thead><tbody>`;
        tasks.forEach(t => {
            let delayDisplay = '-';
            let delayColor = '#666';
            if (t.actual_end && t.planned_end) {
                const diff = Math.round((new Date(t.actual_end) - new Date(t.planned_end)) / (1000*60*60*24));
                delayDisplay = diff > 0 ? `+${diff}d` : diff < 0 ? `${diff}d` : '0d';
                delayColor = diff > 0 ? '#c62828' : '#2e7d32';
            }
            html += `<tr ${t.is_delayed ? 'style="background:#fff8f8"' : ''}>
                <td><strong>${t.name}</strong>${t.rag_context && t.rag_context.length ? `<br><a onclick="show3W1HPopup('${milestoneId}','${t.id}')" style="font-size:10px;color:#e65100;cursor:pointer;text-decoration:underline">📋 ${t.rag_context.length} issue(s)</a>` : ''}</td>
                <td>${t.owner || '-'}</td>
                <td>${t.planned_start || '-'}</td>
                <td>${t.planned_end || '-'}</td>
                <td>${t.actual_start || '-'}</td>
                <td>${t.actual_end || '-'}</td>
                <td style="color:${delayColor};font-weight:600">${delayDisplay}</td>
                <td style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${t.remarks||''}">${t.remarks || '-'}</td>
                <td style="white-space:nowrap">
                    ${t.is_delayed ? `<button class="btn btn-sm" style="background:#fff3e0;color:#e65100;border:1px solid #e65100;font-size:10px" onclick="showAdd3W1HModal('${projectId}','${milestoneId}','${t.id}')" title="Add another 3W1H issue">+ Issue</button>` : ''}
                    <button class="btn btn-sm btn-secondary" onclick="editTaskById('${projectId}','${milestoneId}','${t.id}')">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTaskConfirm('${projectId}','${milestoneId}','${t.id}')">🗑️</button>
                </td>
            </tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color:#c62828;font-size:12px">${e.message}</p>`;
    }
}

// ============ ADD TASK MODAL ============
function showAddTaskModal(projectId, milestoneId) {
    showModal('Add Task', `
        <div class="form-group"><label>Name <span class="required">*</span></label><input id="task-name" placeholder="Task / story name"></div>
        <div class="form-group"><label>Owner</label><input id="task-owner" placeholder="Owner name"></div>
        <div class="form-row">
            <div class="form-group"><label>Planned Start</label><input type="date" id="task-pstart"></div>
            <div class="form-group"><label>Planned End</label><input type="date" id="task-pend"></div>
        </div>
        <div class="form-group"><label>Remarks</label><textarea id="task-remarks" rows="2"></textarea></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitAddTask('${projectId}','${milestoneId}')">Add Task</button></div>
    `);
}

async function submitAddTask(projectId, milestoneId) {
    const body = {
        name: document.getElementById('task-name').value,
        owner: document.getElementById('task-owner').value || null,
        planned_start: document.getElementById('task-pstart').value || null,
        planned_end: document.getElementById('task-pend').value || null,
        remarks: document.getElementById('task-remarks').value || null,
    };
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/milestones/${milestoneId}/tasks`, { method: 'POST', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ EDIT TASK MODAL ============
let _loadedTasks = {}; // milestone_id -> tasks array cache

function editTaskById(projectId, milestoneId, taskId) {
    // Find the task from loaded tasks cache
    const tasks = _loadedTasks[milestoneId] || [];
    const t = tasks.find(task => task.id === taskId);
    if (!t) { showToastNotification('Task not found. Try expanding the milestone again.', 'error'); return; }
    showEditTaskModal(projectId, milestoneId, t);
}

function showEditTaskModal(projectId, milestoneId, t) {
    const hasExistingIssues = t.rag_context && t.rag_context.length > 0;
    const showDelaySection = t.is_delayed && !hasExistingIssues;
    showModal('Edit Task', `
        <div class="form-group"><label>Name <span class="required">*</span></label><input id="etask-name" value="${t.name}"></div>
        <div class="form-group"><label>Owner</label><input id="etask-owner" value="${t.owner||''}"></div>
        <div class="form-row">
            <div class="form-group"><label>Planned Start</label><input type="date" id="etask-pstart" value="${t.planned_start||''}"></div>
            <div class="form-group"><label>Planned End</label><input type="date" id="etask-pend" value="${t.planned_end||''}"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Actual Start</label><input type="date" id="etask-astart" value="${t.actual_start||''}"></div>
            <div class="form-group"><label>Actual End</label><input type="date" id="etask-aend" value="${t.actual_end||''}" onchange="checkTaskDelay()"></div>
        </div>
        <div class="form-group"><label>Remarks</label><textarea id="etask-remarks" rows="2">${t.remarks||''}</textarea></div>
        ${hasExistingIssues ? `<p style="font-size:11px;color:#e65100;margin:8px 0">⚠️ ${t.rag_context.length} issue(s) already logged. Use "+ Issue" button to add more.</p>` : ''}
        <div id="etask-3w1h-section" style="display:${showDelaySection ? 'block' : 'none'};background:#fff3e0;padding:12px;border-radius:6px;border-left:3px solid #e65100;margin-top:8px">
            <p style="font-size:11px;font-weight:600;color:#e65100;margin-bottom:8px">⚠️ Delay detected — 3W1H context required</p>
            <div class="form-group"><label>What (issue) <span class="required">*</span></label><input id="etask-d-what" placeholder="What is the delay/issue?"></div>
            <div class="form-group"><label>Why (root cause) <span class="required">*</span></label><input id="etask-d-why" placeholder="Root cause of delay"></div>
            <div class="form-group"><label>Who (blocking) <span class="required">*</span></label><input id="etask-d-who" placeholder="Person/team blocking"></div>
            <div class="form-group"><label>Owner/Team (action) <span class="required">*</span></label><input id="etask-d-owner" placeholder="Who will resolve this?"></div>
            <div class="form-group"><label>How (recovery plan) <span class="required">*</span></label><input id="etask-d-how" placeholder="Action plan to recover"></div>
            <div class="form-group"><label>ETA <span class="required">*</span></label><input type="date" id="etask-d-eta"></div>
        </div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitEditTask('${projectId}','${milestoneId}','${t.id}')">Save</button></div>
    `);
}

function checkTaskDelay() {
    const pEnd = document.getElementById('etask-pend')?.value;
    const aEnd = document.getElementById('etask-aend')?.value;
    const section = document.getElementById('etask-3w1h-section');
    if (!section) return;
    // Only show if delay detected AND no existing issues already logged
    const hasExistingMsg = document.querySelector('[style*="e65100"]');
    const hasExisting = hasExistingMsg && hasExistingMsg.textContent.includes('issue(s) already logged');
    if (pEnd && aEnd && aEnd > pEnd && !hasExisting) {
        section.style.display = 'block';
    } else {
        section.style.display = 'none';
    }
}

async function submitEditTask(projectId, milestoneId, taskId) {
    const pEnd = document.getElementById('etask-pend').value;
    const aEnd = document.getElementById('etask-aend').value;
    const isDelayed = pEnd && aEnd && aEnd > pEnd;

    const body = {
        name: document.getElementById('etask-name').value,
        owner: document.getElementById('etask-owner').value || null,
        planned_start: document.getElementById('etask-pstart').value || null,
        planned_end: document.getElementById('etask-pend').value || null,
        actual_start: document.getElementById('etask-astart').value || null,
        actual_end: document.getElementById('etask-aend').value || null,
        remarks: document.getElementById('etask-remarks').value || null,
    };

    // Include 3W1H if delay detected
    if (isDelayed) {
        body.delay_what = document.getElementById('etask-d-what').value || null;
        body.delay_why = document.getElementById('etask-d-why').value || null;
        body.delay_who = document.getElementById('etask-d-who').value || null;
        body.delay_owner_team = document.getElementById('etask-d-owner').value || null;
        body.delay_how = document.getElementById('etask-d-how').value || null;
        body.delay_eta = document.getElementById('etask-d-eta').value || null;
    }

    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/milestones/${milestoneId}/tasks/${taskId}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

async function deleteTaskConfirm(projectId, milestoneId, taskId) {
    if (!confirm('Delete this task? This cannot be undone.')) return;
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/milestones/${milestoneId}/tasks/${taskId}`, { method: 'DELETE', headers: mpHeaders() });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ VIEW 3W1H ISSUES POPUP ============
function show3W1HPopup(milestoneId, taskId) {
    const tasks = _loadedTasks[milestoneId] || [];
    const t = tasks.find(tk => tk.id === taskId);
    if (!t || !t.rag_context || !t.rag_context.length) {
        showToastNotification('No issues found', 'warning');
        return;
    }
    const entries = t.rag_context;
    let tableRows = entries.map((rc, i) => `<tr>
        <td>${i + 1}</td>
        <td>${rc.what || '-'}</td>
        <td>${rc.why || '-'}</td>
        <td>${rc.who || '-'}</td>
        <td>${rc.owner_team || '-'}</td>
        <td>${rc.how || '-'}</td>
        <td>${rc.eta || '-'}</td>
        <td><span style="font-size:10px;padding:2px 6px;border-radius:4px;background:${rc.status === 'Resolved' ? '#e8f5e9' : '#fff3e0'};color:${rc.status === 'Resolved' ? '#2e7d32' : '#e65100'}">${rc.status || 'Open'}</span></td>
    </tr>`).join('');

    showModal(`3W1H Issues — ${t.name}`, `
        <div style="overflow-x:auto">
        <table class="data-table" style="font-size:12px">
            <thead><tr><th>#</th><th>What</th><th>Why</th><th>Who (blocking)</th><th>Owner/Team</th><th>How (plan)</th><th>ETA</th><th>Status</th></tr></thead>
            <tbody>${tableRows}</tbody>
        </table>
        </div>
        <div class="btn-group" style="margin-top:12px"><button class="btn btn-secondary" onclick="closeModal()">Close</button></div>
    `);
}

// ============ ADD 3W1H ISSUE MODAL (standalone - for adding parallel issues) ============
function showAdd3W1HModal(projectId, milestoneId, taskId) {
    showModal('Add 3W1H Issue', `
        <p style="font-size:12px;color:#666;margin-bottom:12px">Add another issue/blocker for this delayed task.</p>
        <div class="form-group"><label>What (issue) <span class="required">*</span></label><input id="new3w-what" placeholder="What is the issue?"></div>
        <div class="form-group"><label>Why (root cause) <span class="required">*</span></label><input id="new3w-why" placeholder="Root cause"></div>
        <div class="form-group"><label>Who (blocking) <span class="required">*</span></label><input id="new3w-who" placeholder="Person/team blocking"></div>
        <div class="form-group"><label>Owner/Team (action owner) <span class="required">*</span></label><input id="new3w-owner" placeholder="Who will resolve?"></div>
        <div class="form-group"><label>How (recovery plan) <span class="required">*</span></label><input id="new3w-how" placeholder="Action plan"></div>
        <div class="form-group"><label>ETA <span class="required">*</span></label><input type="date" id="new3w-eta"></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitAdd3W1H('${projectId}','${milestoneId}','${taskId}')">Add Issue</button></div>
    `);
}

async function submitAdd3W1H(projectId, milestoneId, taskId) {
    const body = {
        delay_what: document.getElementById('new3w-what').value,
        delay_why: document.getElementById('new3w-why').value,
        delay_who: document.getElementById('new3w-who').value,
        delay_owner_team: document.getElementById('new3w-owner').value,
        delay_how: document.getElementById('new3w-how').value,
        delay_eta: document.getElementById('new3w-eta').value || null,
    };
    if (!body.delay_what || !body.delay_why || !body.delay_who || !body.delay_owner_team || !body.delay_how || !body.delay_eta) {
        showToastNotification('All 3W1H fields are required', 'warning');
        return;
    }
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/milestones/${milestoneId}/tasks/${taskId}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(e.detail || 'Failed'); }
        closeModal();
        showToastNotification('3W1H issue added', 'success');
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ DEPENDENCIES TAB ============
function renderDependenciesTab(projectId) {
    const deps = mpcp.dependencies;
    return `<div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3>Dependencies</h3>
            <button class="btn btn-primary btn-sm" onclick="showAddDependencyModal('${projectId}')">+ Add Dependency</button>
        </div>
        <table class="data-table"><thead><tr><th>Description</th><th>Owner</th><th>ETA</th><th>Linked To</th><th>Status</th><th>Blocker</th><th>Overdue</th><th>Actions</th></tr></thead><tbody>
        ${deps.map(d => {
            const linkedMs = d.milestone_id ? (mpcp.executionTrack?.milestones?.find(m => m.id === d.milestone_id)?.name || 'Milestone') : 'Project';
            const blockerBadge = d.is_blocker ? '<span style="background:#c62828;color:white;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700">🚫 BLOCKER</span>' : '<span style="color:#999;font-size:11px">-</span>';
            return `<tr class="${d.is_overdue ? 'overdue' : ''}" style="${d.is_blocker ? 'border-left:3px solid #c62828;' : ''}">
            <td>${d.description}</td><td>${d.external_owner}</td><td>${d.cutoff_date}</td>
            <td><span style="font-size:11px;background:${d.milestone_id ? '#e3f2fd' : '#f5f5f5'};padding:2px 6px;border-radius:4px">${linkedMs}</span></td>
            <td><span class="rag-badge ${d.status === 'Resolved' ? 'green' : d.status === 'Escalated' ? 'red' : 'yellow'}">${d.status}</span></td>
            <td>${blockerBadge}</td>
            <td>${d.is_overdue ? '⚠️ Yes' : '-'}</td>
            <td style="white-space:nowrap">
                <button class="btn btn-sm btn-secondary" onclick="showEditDependencyModal('${projectId}','${d.id}')">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="deleteDependencyConfirm('${projectId}','${d.id}')">🗑️</button>
            </td>
        </tr>`;}).join('')}
        ${deps.length === 0 ? '<tr><td colspan="8" style="text-align:center;color:#999">No dependencies.</td></tr>' : ''}
        </tbody></table>
    </div>`;
}

// ============ BUDGET TAB ============
function renderBudgetTab(projectId) {
    const b = mpcp.budget;
    if (!b) return '<div class="card"><p>No budget data.</p></div>';
    const pct = b.approved_budget > 0 ? (b.total_committed / b.approved_budget * 100) : 0;
    const barColor = pct > 100 ? '#c62828' : pct > 80 ? '#f57f17' : '#4caf50';
    const statusLabel = pct > 100 ? 'Over Committed' : pct > 80 ? 'At Risk' : 'On Track';
    const txns = b.transactions || [];
    const txnTypeLabels = { PO_Issued: 'PO Issued', Change_Request: 'Change Request', Spend: 'Spend', Refund: 'Refund' };

    // Quarterly computation
    const qp = b.quarterly_plan || { Q1: 0, Q2: 0, Q3: 0, Q4: 0 };
    const qActual = { Q1: 0, Q2: 0, Q3: 0, Q4: 0 };
    txns.forEach(t => {
        const q = t.quarter || _inferQuarter(t.date);
        if (q && qActual.hasOwnProperty(q)) {
            if (t.transaction_type === 'PO_Issued' || t.transaction_type === 'Change_Request') {
                qActual[q] += t.amount;
            }
        }
    });
    const maxQVal = Math.max(qp.Q1, qp.Q2, qp.Q3, qp.Q4, qActual.Q1, qActual.Q2, qActual.Q3, qActual.Q4, 1);
    const hasQuarterlyData = (qp.Q1 + qp.Q2 + qp.Q3 + qp.Q4) > 0 || (qActual.Q1 + qActual.Q2 + qActual.Q3 + qActual.Q4) > 0;

    const quarterlySection = hasQuarterlyData ? `
        <h4 style="margin-top:20px;margin-bottom:12px">Quarterly Planned vs Actual (PO Committed)</h4>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px">
            ${['Q1','Q2','Q3','Q4'].map(q => {
                const planned = qp[q] || 0;
                const actual = qActual[q] || 0;
                const pctP = maxQVal > 0 ? (planned / maxQVal * 100) : 0;
                const pctA = maxQVal > 0 ? (actual / maxQVal * 100) : 0;
                const overQ = planned > 0 && actual > planned;
                const qLabel = { Q1: 'Q1 (Apr-Jun)', Q2: 'Q2 (Jul-Sep)', Q3: 'Q3 (Oct-Dec)', Q4: 'Q4 (Jan-Mar)' }[q];
                return `<div style="background:#f8f9fa;border-radius:8px;padding:12px;border:1px solid ${overQ ? '#ffcdd2' : '#e0e0e0'}">
                    <div style="font-size:11px;font-weight:600;color:#555;margin-bottom:8px">${qLabel}</div>
                    <div style="display:flex;align-items:flex-end;height:60px;gap:6px;margin-bottom:8px">
                        <div style="flex:1;display:flex;flex-direction:column;align-items:center">
                            <div style="width:100%;background:#bbdefb;border-radius:3px 3px 0 0;height:${Math.max(pctP * 0.6, 2)}px"></div>
                        </div>
                        <div style="flex:1;display:flex;flex-direction:column;align-items:center">
                            <div style="width:100%;background:${overQ ? '#ef5350' : '#4caf50'};border-radius:3px 3px 0 0;height:${Math.max(pctA * 0.6, 2)}px"></div>
                        </div>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:10px;color:#666">
                        <span style="color:#1565c0">Plan: ₹${fmt(planned)}</span>
                        <span style="color:${overQ ? '#c62828' : '#2e7d32'}">Act: ₹${fmt(actual)}</span>
                    </div>
                    ${overQ ? '<div style="font-size:9px;color:#c62828;margin-top:4px;text-align:center">⚠ Over Plan</div>' : ''}
                </div>`;
            }).join('')}
        </div>
        <div style="display:flex;gap:16px;font-size:11px;color:#666;margin-bottom:8px">
            <span><span style="display:inline-block;width:10px;height:10px;background:#bbdefb;border-radius:2px;margin-right:4px;vertical-align:middle"></span>Planned</span>
            <span><span style="display:inline-block;width:10px;height:10px;background:#4caf50;border-radius:2px;margin-right:4px;vertical-align:middle"></span>Actual (PO Committed)</span>
        </div>
    ` : '';

    return `<div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3>Budget</h3>
            <div style="display:flex;gap:8px">
                <button class="btn btn-sm btn-primary" onclick="showAddTransactionModal('${projectId}')">+ Add Transaction</button>
                <button class="btn btn-sm btn-secondary" onclick="showEditBudgetModal('${projectId}')">Edit Budget</button>
            </div>
        </div>
        <div class="metrics-grid" style="grid-template-columns:repeat(4,1fr)">
            <div class="metric-card"><h4>Approved Budget</h4><div class="value">₹${fmt(b.approved_budget)}</div></div>
            <div class="metric-card"><h4>Internal Estimate</h4><div class="value">₹${fmt(b.internal_estimate)}</div></div>
            <div class="metric-card"><h4>Total Value of PO Issued</h4><div class="value">₹${fmt(b.total_committed)}</div></div>
            <div class="metric-card"><h4>Remaining</h4><div class="value" style="color:${b.remaining < 0 ? '#c62828' : '#2e7d32'}">₹${fmt(b.remaining)}</div></div>
        </div>
        <div style="margin:16px 0">
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px"><span>Utilization</span><span style="font-weight:600;color:${barColor}">${pct.toFixed(0)}% — ${statusLabel}</span></div>
            <div style="height:10px;background:#e0e0e0;border-radius:5px;overflow:hidden"><div style="height:100%;width:${Math.min(pct,100)}%;background:${barColor};border-radius:5px"></div></div>
        </div>
        ${b.remarks ? `<div style="font-size:12px;color:#666;margin-bottom:12px">Remarks: ${b.remarks}</div>` : ''}
        ${quarterlySection}
        <h4 style="margin-top:16px;margin-bottom:8px">Transactions</h4>
        <table class="data-table"><thead><tr><th>Date</th><th>Type</th><th>PO/GRN#</th><th>Vendor</th><th>Amount</th><th>Quarter</th><th>Remarks</th></tr></thead><tbody>
        ${txns.length === 0 ? '<tr><td colspan="7" style="text-align:center;color:#999">No transactions yet.</td></tr>' : txns.map(t => `<tr>
            <td>${t.date || ''}</td>
            <td>${txnTypeLabels[t.transaction_type] || t.transaction_type}</td>
            <td>${t.po_number || '-'}</td>
            <td>${t.vendor || '-'}</td>
            <td>₹${fmt(t.amount)}</td>
            <td>${t.quarter || _inferQuarter(t.date) || '-'}</td>
            <td>${t.remarks || ''}</td>
        </tr>`).join('')}
        </tbody></table>
    </div>`;
}

function _inferQuarter(dateStr) {
    if (!dateStr) return '';
    const m = new Date(dateStr).getMonth(); // 0-indexed
    if (m >= 3 && m <= 5) return 'Q1';
    if (m >= 6 && m <= 8) return 'Q2';
    if (m >= 9 && m <= 11) return 'Q3';
    return 'Q4'; // Jan, Feb, Mar
}

// ============ TOAST NOTIFICATIONS (replaces browser alert) ============
function showToastNotification(message, type = 'error', actionLabel = null, actionRoute = null) {
    let container = document.getElementById('mpcp-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'mpcp-toast-container';
        container.style.cssText = 'position:fixed;top:80px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;max-width:400px;';
        document.body.appendChild(container);
    }
    const colors = { error: '#c62828', success: '#2e7d32', warning: '#f57f17', info: '#1565c0' };
    const icons = { error: '❌', success: '✅', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.style.cssText = `background:white;border-left:4px solid ${colors[type]};padding:14px 18px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.15);font-size:13px;display:flex;flex-direction:column;gap:8px;animation:slideIn 0.3s ease;`;
    let html = `<div style="display:flex;align-items:flex-start;gap:8px"><span>${icons[type]}</span><span>${message}</span></div>`;
    if (actionLabel && actionRoute) {
        html += `<a onclick="navigateTo('${actionRoute}');this.parentElement.remove();" style="color:${colors.info};font-weight:600;cursor:pointer;font-size:12px;margin-left:24px;">${actionLabel} →</a>`;
    }
    toast.innerHTML = html;
    container.appendChild(toast);
    setTimeout(() => { if (toast.parentElement) toast.remove(); }, 6000);
}

// ============ MODALS ============
function showModal(title, body) {
    let overlay = document.getElementById('mpcp-modal-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'mpcp-modal-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:9000;display:flex;align-items:center;justify-content:center';
        document.body.appendChild(overlay);
    }
    overlay.innerHTML = `<div style="background:white;border-radius:12px;padding:24px;max-width:500px;width:90%;max-height:80vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,0.2)">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><h3>${title}</h3><button onclick="closeModal()" style="border:none;background:none;font-size:20px;cursor:pointer">✕</button></div>
        ${body}
    </div>`;
    overlay.style.display = 'flex';
}

function closeModal() {
    const overlay = document.getElementById('mpcp-modal-overlay');
    if (overlay) overlay.style.display = 'none';
}

function refreshCurrentMPCPView() {
    renderMPCPTracker(window.location.hash.slice(1));
    // Auto-refresh changelog if it was visible
    setTimeout(() => {
        const clTab = document.getElementById('mpcp-tab-changelog');
        if (clTab && clTab.style.display !== 'none') loadChangeLogData();
    }, 300);
}

// ============ CREATE MP MODAL ============
function showCreateMPModal() {
    showModal('Create Managing Point', `
        <div class="form-group"><label>Code <span class="required">*</span></label><input id="mp-code" placeholder="e.g. A3, B1"></div>
        <div class="form-group"><label>Name <span class="required">*</span></label><input id="mp-name" placeholder="MP name"></div>
        <div class="form-row">
            <div class="form-group"><label>Theme <span class="required">*</span></label><select id="mp-theme"><option value="A">A - Customer Satisfaction</option><option value="B">B - Profit & Profitability</option><option value="C">C - Business Growth</option><option value="D">D - New Product Development</option><option value="E">E - Effectiveness</option><option value="F">F - Digitalization & AI</option><option value="Z">Z - Others (Non-MPCP)</option></select></div>
            <div class="form-group"><label>Owner <span class="required">*</span></label><input id="mp-owner" placeholder="Owner name"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>BU <span class="required">*</span></label><select id="mp-bu"><option value="IND-2W">IND-2W</option><option value="3W/CMB">3W/CMB</option><option value="IB">IB</option></select></div>
        </div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitCreateMP()">Create</button></div>
    `);
}

async function submitCreateMP() {
    const body = {
        code: document.getElementById('mp-code').value.toUpperCase().trim(),
        name: document.getElementById('mp-name').value,
        theme: document.getElementById('mp-theme').value,
        owner: document.getElementById('mp-owner').value,
        lob: document.getElementById('mp-bu').value,
        bu: document.getElementById('mp-bu').value,
    };
    try {
        const resp = await fetch(`${MPCP_API}/mps`, { method: 'POST', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ CREATE CP MODAL ============
function showCreateCPModal(mpId) {
    // Get parent MP code to auto-prefix
    const parentMp = mpcp.currentMp || mpcp.mps.find(m => m.id === mpId);
    const prefix = parentMp ? parentMp.code + '.' : '';
    showModal('Create Check Point', `
        <div class="form-group"><label>Code <span class="required">*</span></label>
            <div style="display:flex;align-items:center;gap:0">
                <span style="background:#e8eaf6;padding:9px 12px;border:1.5px solid #ddd;border-right:none;border-radius:8px 0 0 8px;font-size:13px;font-weight:600;color:#1a237e">${prefix}</span>
                <input id="cp-code-suffix" placeholder="1" style="border-radius:0 8px 8px 0;border-left:none;width:80px">
            </div>
        </div>
        <div class="form-group"><label>Name <span class="required">*</span></label><input id="cp-name" placeholder="CP name"></div>
        <div class="form-group"><label>Owner <span class="required">*</span></label><input id="cp-owner" placeholder="Owner name"></div>
        <div class="form-group"><label>Description</label><textarea id="cp-desc" rows="2"></textarea></div>
        <div class="form-row">
            <div class="form-group"><label>Domain</label><select id="cp-domain"><option value="">-</option><option>All</option><option>Shop</option><option>Buy</option><option>Own</option><option>Parts</option></select></div>
            <div class="form-group"><label>Stream</label><select id="cp-stream"><option value="">-</option><option>All</option><option>D2C</option><option>Channel Partner</option><option>Platform Services</option></select></div>
        </div>
        <div class="form-group"><label>Target Quarter</label><select id="cp-quarter"><option value="">-</option><option>Q1</option><option>Q2</option><option>Q3</option><option>Q4</option></select></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitCreateCP('${mpId}','${prefix}')">Create</button></div>
    `);
}

async function submitCreateCP(mpId, prefix) {
    const body = {
        code: prefix + document.getElementById('cp-code-suffix').value.trim(),
        name: document.getElementById('cp-name').value,
        owner: document.getElementById('cp-owner').value,
        description: document.getElementById('cp-desc').value || null,
        domain: document.getElementById('cp-domain').value || null,
        stream: document.getElementById('cp-stream').value || null,
        target_quarter: document.getElementById('cp-quarter').value || null,
    };
    try {
        const resp = await fetch(`${MPCP_API}/mps/${mpId}/cps`, { method: 'POST', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ ADD MILESTONE MODAL ============
function showAddMilestoneModal(projectId) {
    showModal('Add Milestone', `
        <div class="form-group"><label>Name <span class="required">*</span></label><input id="ms-name" placeholder="Milestone name"></div>
        <div class="form-group"><label>Vendor</label><select id="ms-vendor"><option value="">-</option><option>Exathought</option><option>Deloitte</option><option>TVSD</option><option>Evontech</option><option>Autovyn</option></select></div>
        <div class="form-row">
            <div class="form-group"><label>Planned Start</label><input type="date" id="ms-start"></div>
            <div class="form-group"><label>Planned End</label><input type="date" id="ms-end"></div>
        </div>
        <div class="form-group"><label>Remarks</label><textarea id="ms-remarks" rows="2"></textarea></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitAddMilestone('${projectId}')">Add</button></div>
    `);
}

async function submitAddMilestone(projectId) {
    const body = {
        name: document.getElementById('ms-name').value,
        vendor: document.getElementById('ms-vendor').value || "",
        planned_start: document.getElementById('ms-start').value || null,
        planned_end: document.getElementById('ms-end').value || null,
        remarks: document.getElementById('ms-remarks').value || null,
    };
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/milestones`, { method: 'POST', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ EDIT MILESTONE MODAL ============
function showEditMilestoneModal(projectId, milestoneIdx) {
    const m = mpcp.executionTrack.milestones[milestoneIdx];
    if (!m) { showToastNotification('Milestone not found', 'error'); return; }
    const rc = m.rag_context || {};
    const isDelayed = m.is_delayed;
    showModal('Edit Milestone', `
        <div class="form-group"><label>Name <span class="required">*</span></label><input id="ems-name" value="${m.name}"></div>
        <div class="form-group"><label>Vendor</label><select id="ems-vendor"><option value="" ${!m.vendor?'selected':''}>-</option><option ${m.vendor==='Exathought'?'selected':''}>Exathought</option><option ${m.vendor==='Deloitte'?'selected':''}>Deloitte</option><option ${m.vendor==='TVSD'?'selected':''}>TVSD</option><option ${m.vendor==='Evontech'?'selected':''}>Evontech</option><option ${m.vendor==='Autovyn'?'selected':''}>Autovyn</option></select></div>
        <div class="form-row">
            <div class="form-group"><label>Planned Start</label><input type="date" id="ems-pstart" value="${m.planned_start||''}"></div>
            <div class="form-group"><label>Planned End</label><input type="date" id="ems-pend" value="${m.planned_end||''}"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Actual Start</label><input type="date" id="ems-astart" value="${m.actual_start||''}"></div>
            <div class="form-group"><label>Actual End</label><input type="date" id="ems-aend" value="${m.actual_end||''}" onchange="checkMilestoneDelay()"></div>
        </div>
        <div class="form-group"><label>Remarks</label><textarea id="ems-remarks" rows="2">${m.remarks||''}</textarea></div>
        <div id="ems-3w1h-section" style="display:${isDelayed ? 'block' : 'none'};background:#fff3e0;padding:12px;border-radius:6px;border-left:3px solid #e65100;margin-top:8px">
            <p style="font-size:11px;font-weight:600;color:#e65100;margin-bottom:8px">⚠️ Delay detected — 3W1H context required</p>
            <div class="form-group"><label>What (issue) <span class="required">*</span></label><input id="ems-d-what" value="${rc.what||''}" placeholder="What is the delay/issue?"></div>
            <div class="form-group"><label>Why (root cause) <span class="required">*</span></label><input id="ems-d-why" value="${rc.why||''}" placeholder="Root cause of delay"></div>
            <div class="form-group"><label>Who (blocking) <span class="required">*</span></label><input id="ems-d-who" value="${rc.who||''}" placeholder="Person/team blocking"></div>
            <div class="form-group"><label>Owner/Team (action) <span class="required">*</span></label><input id="ems-d-owner" value="${rc.owner_team||''}" placeholder="Who will resolve this?"></div>
            <div class="form-group"><label>How (recovery plan) <span class="required">*</span></label><input id="ems-d-how" value="${rc.how||''}" placeholder="Action plan to recover"></div>
            <div class="form-group"><label>ETA <span class="required">*</span></label><input type="date" id="ems-d-eta" value="${rc.eta||''}"></div>
        </div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitEditMilestone('${projectId}','${m.id}')">Save</button></div>
    `);
}

function checkMilestoneDelay() {
    const pEnd = document.getElementById('ems-pend')?.value;
    const aEnd = document.getElementById('ems-aend')?.value;
    const section = document.getElementById('ems-3w1h-section');
    if (section && pEnd && aEnd && aEnd > pEnd) {
        section.style.display = 'block';
    } else if (section) {
        section.style.display = 'none';
    }
}

async function submitEditMilestone(projectId, milestoneId) {
    const pEnd = document.getElementById('ems-pend').value;
    const aEnd = document.getElementById('ems-aend').value;
    const isDelayed = pEnd && aEnd && aEnd > pEnd;

    const body = {
        name: document.getElementById('ems-name').value,
        vendor: document.getElementById('ems-vendor').value || null,
        planned_start: document.getElementById('ems-pstart').value || null,
        planned_end: document.getElementById('ems-pend').value || null,
        actual_start: document.getElementById('ems-astart').value || null,
        actual_end: document.getElementById('ems-aend').value || null,
        remarks: document.getElementById('ems-remarks').value || null,
    };

    // Include 3W1H if delay detected
    if (isDelayed) {
        body.delay_what = document.getElementById('ems-d-what').value || null;
        body.delay_why = document.getElementById('ems-d-why').value || null;
        body.delay_who = document.getElementById('ems-d-who').value || null;
        body.delay_owner_team = document.getElementById('ems-d-owner').value || null;
        body.delay_how = document.getElementById('ems-d-how').value || null;
        body.delay_eta = document.getElementById('ems-d-eta').value || null;
    }

    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/milestones/${milestoneId}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

async function deleteMilestoneConfirm(projectId, milestoneId) {
    if (!confirm('Delete this milestone? This cannot be undone.')) return;
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/milestones/${milestoneId}`, { method: 'DELETE', headers: mpHeaders() });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        navigateTo('#mpcp-tracker/projects/' + projectId);
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ ADD DEPENDENCY MODAL ============
function showAddDependencyModal(projectId) {
    // Build milestone options from execution track
    const milestones = mpcp.executionTrack?.milestones || [];
    const msOptions = milestones.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
    showModal('Add Dependency', `
        <div class="form-group"><label>Description <span class="required">*</span></label><input id="dep-desc" placeholder="What is the dependency?"></div>
        <div class="form-group"><label>Owner <span class="required">*</span></label><input id="dep-owner" placeholder="Who owns this? (person/team)"></div>
        <div class="form-group"><label>ETA / Cutoff Date <span class="required">*</span></label><input type="date" id="dep-cutoff"></div>
        <div class="form-group"><label>Linked Milestone</label><select id="dep-milestone"><option value="">Project level (no specific milestone)</option>${msOptions}</select></div>
        <div class="form-group"><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" id="dep-blocker" style="width:auto;margin:0"> <span style="color:#c62828;font-weight:600">🚫 Mark as Blocker</span> <span style="font-weight:400;color:#666;font-size:11px">(blocking project progress)</span></label></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitAddDependency('${projectId}')">Add</button></div>
    `);
}

async function submitAddDependency(projectId) {
    const body = {
        description: document.getElementById('dep-desc').value,
        external_owner: document.getElementById('dep-owner').value,
        cutoff_date: document.getElementById('dep-cutoff').value,
        milestone_id: document.getElementById('dep-milestone').value || null,
        is_blocker: document.getElementById('dep-blocker').checked,
    };
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/dependencies`, { method: 'POST', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ EDIT BUDGET MODAL ============
function showEditBudgetModal(projectId) {
    const b = mpcp.budget || {};
    const qp = b.quarterly_plan || { Q1: 0, Q2: 0, Q3: 0, Q4: 0 };
    showModal('Edit Budget', `
        <div class="form-row">
            <div class="form-group"><label>Approved Budget (₹)</label><input type="number" id="bud-approved" value="${b.approved_budget || 0}"></div>
            <div class="form-group"><label>Internal Estimate (₹)</label><input type="number" id="bud-internal" value="${b.internal_estimate || 0}"></div>
        </div>
        <h4 style="margin:12px 0 8px;font-size:13px;color:#555">Quarterly Planned Allocation (₹)</h4>
        <div class="form-row" style="grid-template-columns:repeat(4,1fr)">
            <div class="form-group"><label>Q1 (Apr-Jun)</label><input type="number" id="bud-q1" value="${qp.Q1 || 0}" min="0"></div>
            <div class="form-group"><label>Q2 (Jul-Sep)</label><input type="number" id="bud-q2" value="${qp.Q2 || 0}" min="0"></div>
            <div class="form-group"><label>Q3 (Oct-Dec)</label><input type="number" id="bud-q3" value="${qp.Q3 || 0}" min="0"></div>
            <div class="form-group"><label>Q4 (Jan-Mar)</label><input type="number" id="bud-q4" value="${qp.Q4 || 0}" min="0"></div>
        </div>
        <div class="form-group"><label>Remarks</label><textarea id="bud-remarks" rows="2">${b.remarks || ''}</textarea></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitBudget('${projectId}')">Save</button></div>
    `);
}

async function submitBudget(projectId) {
    const body = {
        approved_budget: parseFloat(document.getElementById('bud-approved').value) || 0,
        internal_estimate: parseFloat(document.getElementById('bud-internal').value) || 0,
        quarterly_plan: {
            Q1: parseFloat(document.getElementById('bud-q1').value) || 0,
            Q2: parseFloat(document.getElementById('bud-q2').value) || 0,
            Q3: parseFloat(document.getElementById('bud-q3').value) || 0,
            Q4: parseFloat(document.getElementById('bud-q4').value) || 0,
        },
        remarks: document.getElementById('bud-remarks').value || null,
    };
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/budget`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ CHANGE LOG TAB ============
function renderChangeLogTab(projectId) {
    return `<div class="card">
        <h3>📝 Change Log</h3>
        <p class="subtitle">History of all changes made to this project</p>
        <div id="changelog-content" style="margin-top:12px;">
            <p style="color:#666;font-size:12px;">Click this tab to load change history...</p>
        </div>
    </div>`;
}

async function loadChangeLogData(page = 1) {
    const container = document.getElementById('changelog-content');
    const projectId = mpcp.currentProjectId;
    if (!container || !projectId) return;
    container.innerHTML = '<p style="color:#1565c0;font-size:12px;"><span class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px;"></span> Loading change history...</p>';

    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/changelog?page=${page}&page_size=15`, { headers: mpHeaders() });
        if (!resp.ok) throw new Error('Failed to load');
        const data = await resp.json();
        const entries = data.entries || [];
        const totalPages = data.total_pages || 1;
        const currentPage = data.page || 1;
        const total = data.total || 0;

        if (entries.length === 0 && currentPage === 1) {
            container.innerHTML = '<p style="color:#999;font-size:12px;">No changes recorded yet.</p>';
            return;
        }

        let paginationHtml = '';
        if (totalPages > 1) {
            paginationHtml = `<div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:8px;border-top:1px solid #eee;">
                <span style="font-size:11px;color:#666;">Showing page ${currentPage} of ${totalPages} (${total} total changes)</span>
                <div style="display:flex;gap:6px;">
                    ${currentPage > 1 ? `<button class="btn btn-sm btn-secondary" onclick="loadChangeLogData(${currentPage - 1})">← Prev</button>` : ''}
                    ${currentPage < totalPages ? `<button class="btn btn-sm btn-secondary" onclick="loadChangeLogData(${currentPage + 1})">Next →</button>` : ''}
                </div>
            </div>`;
        }

        container.innerHTML = `
            <div style="font-size:11px;color:#888;margin-bottom:8px;">${total} change${total !== 1 ? 's' : ''} recorded</div>
            <div style="overflow-x:auto;max-height:350px;overflow-y:auto;">
                <table class="data-table" style="font-size:12px;">
                    <thead><tr><th>Date</th><th>Changed By</th><th>Field</th><th>Old Value</th><th>New Value</th><th>Context</th></tr></thead>
                    <tbody>${entries.map(e => {
                        const ts = e.timestamp ? new Date(e.timestamp).toLocaleString('en-IN', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '-';
                        return `<tr>
                            <td style="white-space:nowrap">${ts}</td>
                            <td>${e.changed_by || '-'}</td>
                            <td><strong>${e.field || '-'}</strong></td>
                            <td style="color:#c62828">${e.old_value || '<em style="color:#999">empty</em>'}</td>
                            <td style="color:#2e7d32">${e.new_value || '<em style="color:#999">empty</em>'}</td>
                            <td style="color:#666;font-size:11px">${e.context || '-'}</td>
                        </tr>`;
                    }).join('')}</tbody>
                </table>
            </div>
            ${paginationHtml}
        `;
    } catch (e) {
        container.innerHTML = `<p style="color:#c62828;font-size:12px;">Failed to load change history: ${e.message}</p>`;
    }
}

// ============ ADD TRANSACTION MODAL ============
function showAddTransactionModal(projectId) {
    showModal('Add Transaction', `
        <div class="form-group"><label>Type <span class="required">*</span></label><select id="txn-type"><option value="PO_Issued">PO Issued</option><option value="Change_Request">Change Request</option><option value="Spend">Spend</option><option value="Refund">Refund</option></select></div>
        <div class="form-row">
            <div class="form-group"><label>PO/GRN Number</label><input id="txn-po" placeholder="PO/GRN#"></div>
            <div class="form-group"><label>Vendor</label><input id="txn-vendor" placeholder="Vendor name"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Amount (₹) <span class="required">*</span></label><input type="number" id="txn-amount" min="0.01" step="0.01"></div>
            <div class="form-group"><label>Date <span class="required">*</span></label><input type="date" id="txn-date" value="${new Date().toISOString().slice(0,10)}"></div>
        </div>
        <div class="form-group"><label>Quarter</label><select id="txn-quarter"><option value="">-</option><option value="Q1">Q1 (Apr-Jun)</option><option value="Q2">Q2 (Jul-Sep)</option><option value="Q3">Q3 (Oct-Dec)</option><option value="Q4">Q4 (Jan-Mar)</option></select></div>
        <div class="form-group"><label>Remarks</label><textarea id="txn-remarks" rows="2"></textarea></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitAddTransaction('${projectId}')">Add</button></div>
    `);
}

async function submitAddTransaction(projectId) {
    const body = {
        transaction_type: document.getElementById('txn-type').value,
        po_number: document.getElementById('txn-po').value || null,
        vendor: document.getElementById('txn-vendor').value || null,
        amount: parseFloat(document.getElementById('txn-amount').value),
        date: document.getElementById('txn-date').value,
        quarter: document.getElementById('txn-quarter').value || null,
        remarks: document.getElementById('txn-remarks').value || null,
    };
    if (!body.amount || body.amount <= 0) { showToastNotification('Amount must be greater than 0', 'error'); return; }
    if (!body.date) { showToastNotification('Date is required', 'error'); return; }
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/budget/transactions`, { method: 'POST', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ RAG UPDATE MODAL ============
function showRAGModal(entityType, entityId, currentStatus) {
    showModal('Update RAG Status', `
        <div class="form-group"><label>Status <span class="required">*</span></label>
            <div style="display:flex;gap:8px;margin-top:4px">
                <label style="cursor:pointer"><input type="radio" name="rag-status" value="Green" ${currentStatus==='Green'?'checked':''} onchange="toggleRAGFields()"> 🟢 Green</label>
                <label style="cursor:pointer"><input type="radio" name="rag-status" value="Yellow" ${currentStatus==='Yellow'?'checked':''} onchange="toggleRAGFields()"> 🟡 Yellow</label>
                <label style="cursor:pointer"><input type="radio" name="rag-status" value="Red" ${currentStatus==='Red'?'checked':''} onchange="toggleRAGFields()"> 🔴 Red</label>
            </div>
        </div>
        <div id="rag-3w1h" style="display:${currentStatus !== 'Green' ? 'block' : 'none'}">
            <div class="form-group"><label>What (issue) <span class="required">*</span></label><input id="rag-what" placeholder="Describe the issue"></div>
            <div class="form-group"><label>Why (root cause) <span class="required">*</span></label><input id="rag-why" placeholder="Root cause"></div>
            <div class="form-group"><label>Who (responsible/blocking) <span class="required">*</span></label><input id="rag-who" placeholder="Person/team blocking"></div>
            <div class="form-group"><label>Owner/Team (action owner) <span class="required">*</span></label><input id="rag-owner-team" placeholder="Who will resolve this?"></div>
            <div class="form-group"><label>How (recovery plan) <span class="required">*</span></label><input id="rag-how" placeholder="Action plan"></div>
            <div class="form-group"><label>ETA <span class="required">*</span></label><input type="date" id="rag-eta"></div>
        </div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitRAG('${entityType}','${entityId}')">Update</button></div>
    `);
}

function toggleRAGFields() {
    const status = document.querySelector('input[name="rag-status"]:checked')?.value;
    document.getElementById('rag-3w1h').style.display = status !== 'Green' ? 'block' : 'none';
}

async function submitRAG(entityType, entityId) {
    const status = document.querySelector('input[name="rag-status"]:checked')?.value;
    if (!status) { showToastNotification('Please select a RAG status', 'warning'); return; }
    const body = { status };
    if (status !== 'Green') {
        body.what = document.getElementById('rag-what').value;
        body.why = document.getElementById('rag-why').value;
        body.who = document.getElementById('rag-who').value;
        body.owner_team = document.getElementById('rag-owner-team').value;
        body.how = document.getElementById('rag-how').value;
        body.eta = document.getElementById('rag-eta').value;
    }
    try {
        const resp = await fetch(`${MPCP_API}/rag/${entityType}/${entityId}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ STAGE EDIT MODAL ============
function showStageEditModal(projectId, stage, stageOrder) {
    // Get current stage data from the loaded process track
    const stageData = mpcp.processTrack?.stages?.find(s => s.stage === stage) || {};
    const curStatus = stageData.status || 'Not_Started';
    const curPlanned = stageData.planned_date || '';
    const curActual = stageData.actual_date || '';
    const curRemarks = stageData.remarks || '';
    const curSkip = stageData.skip_reason || '';
    showModal(`Update Stage: ${stage}`, `
        <div class="form-group"><label>Status <span class="required">*</span></label>
            <select id="stage-status">
                <option value="Not_Started" ${curStatus==='Not_Started'?'selected':''}>Not Started</option>
                <option value="In_Progress" ${curStatus==='In_Progress'?'selected':''}>In Progress</option>
                <option value="Completed" ${curStatus==='Completed'?'selected':''}>Completed</option>
                <option value="Skipped" ${curStatus==='Skipped'?'selected':''}>Skipped</option>
            </select>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Planned Date</label><input type="date" id="stage-planned" value="${curPlanned}"></div>
            <div class="form-group"><label>Actual Date</label><input type="date" id="stage-actual" value="${curActual}"></div>
        </div>
        <div class="form-group"><label>Remarks</label><input id="stage-remarks" value="${curRemarks}" placeholder="Notes"></div>
        <div class="form-group"><label>Skip Reason (if Skipped)</label><input id="stage-skip" value="${curSkip}" placeholder="Why skipped?"></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitStageUpdate('${projectId}','${stage}')">Update</button></div>
    `);
}

async function submitStageUpdate(projectId, stage) {
    const body = {
        status: document.getElementById('stage-status').value,
        planned_date: document.getElementById('stage-planned').value || null,
        actual_date: document.getElementById('stage-actual').value || null,
        remarks: document.getElementById('stage-remarks').value || null,
        skip_reason: document.getElementById('stage-skip').value || null,
    };
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/process-track/${stage}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// ============ INLINE DATE EDITING ============
function inlineDateEdit(cell, projectId, stage, field, currentValue) {
    // Prevent double-opening
    if (cell.querySelector('input[type=date]')) return;

    const display = cell.querySelector('.date-display');
    if (display) display.style.display = 'none';

    const input = document.createElement('input');
    input.type = 'date';
    input.value = currentValue || '';
    input.style.cssText = 'font-size:12px;padding:4px 6px;border:1.5px solid #3949ab;border-radius:6px;outline:none;width:130px;background:#f8f9ff;';
    cell.appendChild(input);
    input.focus();

    // Open the native date picker automatically
    try { input.showPicker(); } catch(e) {}

    const save = async () => {
        const newVal = input.value || null;
        // Only save if value actually changed
        if (newVal === (currentValue || null)) {
            cleanup();
            return;
        }
        try {
            // Build minimal update body — only send the changed field
            const stageData = mpcp.processTrack?.stages?.find(s => s.stage === stage) || {};
            const body = {
                status: stageData.status || 'Not_Started',
                planned_date: field === 'planned_date' ? newVal : (stageData.planned_date || null),
                actual_date: field === 'actual_date' ? newVal : (stageData.actual_date || null),
                remarks: stageData.remarks || null,
                skip_reason: stageData.skip_reason || null,
            };
            const resp = await fetch(`${MPCP_API}/projects/${projectId}/process-track/${stage}`, {
                method: 'PUT',
                headers: mpHeadersJson(),
                body: JSON.stringify(body),
            });
            if (!resp.ok) {
                const e = await resp.json();
                throw new Error(Array.isArray(e.detail) ? e.detail.map(d => d.msg || d.error).join(', ') : e.detail || 'Failed');
            }
            showToastNotification(`${field === 'planned_date' ? 'Planned' : 'Actual'} date updated`, 'success');
            refreshCurrentMPCPView();
        } catch (e) {
            showToastNotification(e.message, 'error');
            cleanup();
        }
    };

    const cleanup = () => {
        if (input.parentNode) input.remove();
        if (display) display.style.display = '';
    };

    input.addEventListener('change', save);
    input.addEventListener('blur', () => {
        // Small delay to allow change event to fire first
        setTimeout(() => { if (input.parentNode) cleanup(); }, 150);
    });
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') cleanup();
    });
}

// ============ UTILITY ============
function fmt(num) {
    if (!num && num !== 0) return '0';
    if (num >= 10000000) return (num / 10000000).toFixed(1) + 'Cr';
    if (num >= 100000) return (num / 100000).toFixed(1) + 'L';
    if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
    return num.toFixed(0);
}


// ============ BULK UPLOAD ============
async function downloadHierarchyTemplate() {
    try {
        const resp = await fetch(`${MPCP_API}/templates/hierarchy-upload`, { headers: mpHeaders() });
        if (!resp.ok) throw new Error('Download failed');
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'MPCP_Hierarchy_Template.xlsx';
        a.click();
        URL.revokeObjectURL(url);
    } catch(e) { showToastNotification(e.message, 'error'); }
}

async function handleBulkUpload(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const container = document.getElementById('mpcp-container');
    container.innerHTML = '<div class="card"><p>⏳ Uploading and processing...</p></div>';

    try {
        const resp = await fetch(`${MPCP_API}/bulk-upload`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('auth_token') || 'demo-token') },
            body: formData,
        });
        const result = await resp.json();
        if (!resp.ok) throw new Error(result.detail || 'Upload failed');

        let html = `<div class="card"><h3>✅ Bulk Upload Complete</h3>
            <div class="metrics-grid" style="margin-top:12px">
                <div class="metric-card"><h4>MPs Created</h4><div class="value">${result.created_mps}</div></div>
                <div class="metric-card"><h4>CPs Created</h4><div class="value">${result.created_cps}</div></div>
                <div class="metric-card"><h4>Projects Created</h4><div class="value">${result.created_projects}</div></div>
            </div>`;
        if (result.errors && result.errors.length > 0) {
            html += `<div style="margin-top:16px"><h4 style="color:#c62828">⚠️ Errors (${result.errors.length})</h4>
                <table class="data-table"><thead><tr><th>Sheet</th><th>Row</th><th>Error</th></tr></thead><tbody>
                ${result.errors.map(e => `<tr><td>${e.sheet}</td><td>${e.row}</td><td>${e.error}</td></tr>`).join('')}
                </tbody></table></div>`;
        }
        html += `<div style="margin-top:16px"><button class="btn btn-primary" onclick="navigateTo('#mpcp-tracker/mps')">View Managing Points</button></div></div>`;
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<div class="card"><p style="color:#c62828">❌ Upload Failed: ${e.message}</p>
            <button class="btn btn-secondary" onclick="navigateTo('#mpcp-tracker/mps')" style="margin-top:12px">Back</button></div>`;
    }
    // Reset input so same file can be re-uploaded
    input.value = '';
}


// ============ EDIT MP MODAL ============
function showEditMPModal(mpId) {
    const mp = mpcp.mps.find(m => m.id === mpId);
    if (!mp) return;
    showModal('Edit Managing Point', `
        <div class="form-group"><label>Code</label><input id="emp-code" value="${mp.code}"></div>
        <div class="form-group"><label>Name</label><input id="emp-name" value="${mp.name}"></div>
        <div class="form-row">
            <div class="form-group"><label>Theme</label><select id="emp-theme"><option value="A" ${mp.theme==='A'?'selected':''}>A - Customer Satisfaction</option><option value="B" ${mp.theme==='B'?'selected':''}>B - Profit & Profitability</option><option value="C" ${mp.theme==='C'?'selected':''}>C - Business Growth</option><option value="D" ${mp.theme==='D'?'selected':''}>D - New Product Development</option><option value="E" ${mp.theme==='E'?'selected':''}>E - Effectiveness</option><option value="F" ${mp.theme==='F'?'selected':''}>F - Digitalization & AI</option><option value="Z" ${mp.theme==='Z'?'selected':''}>Z - Others (Non-MPCP)</option></select></div>
            <div class="form-group"><label>Owner</label><input id="emp-owner" value="${mp.owner}"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>BU</label><select id="emp-bu"><option value="IND-2W" ${mp.bu==='IND-2W'?'selected':''}>IND-2W</option><option value="3W/CMB" ${mp.bu==='3W/CMB'?'selected':''}>3W/CMB</option><option value="IB" ${mp.bu==='IB'?'selected':''}>IB</option></select></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>UOM</label><input id="emp-uom" value="${mp.uom||''}"></div>
            <div class="form-group"><label>From</label><input id="emp-from" value="${mp.target_from||''}"></div>
            <div class="form-group"><label>To</label><input id="emp-to" value="${mp.target_to||''}"></div>
        </div>
        <div class="btn-group"><button class="btn btn-danger btn-sm" onclick="deleteMPConfirm('${mpId}')">Delete</button><div><button class="btn btn-secondary" onclick="closeModal()">Cancel</button> <button class="btn btn-primary" onclick="submitEditMP('${mpId}')">Save</button></div></div>
    `);
}

async function submitEditMP(mpId) {
    const body = {
        code: document.getElementById('emp-code').value,
        name: document.getElementById('emp-name').value,
        theme: document.getElementById('emp-theme').value,
        owner: document.getElementById('emp-owner').value,
        lob: document.getElementById('emp-bu').value,
        bu: document.getElementById('emp-bu').value,
        uom: document.getElementById('emp-uom').value || null,
        target_from: document.getElementById('emp-from').value || null,
        target_to: document.getElementById('emp-to').value || null,
    };
    try {
        const resp = await fetch(`${MPCP_API}/mps/${mpId}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

async function deleteMPConfirm(mpId) {
    if (!confirm('Delete this Managing Point? It must have 0 Check Points.')) return;
    try {
        const resp = await fetch(`${MPCP_API}/mps/${mpId}`, { method: 'DELETE', headers: mpHeaders() });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}


// ============ EDIT CP MODAL ============
function showEditCPModal(cpId) {
    const cp = mpcp.cps.find(c => c.id === cpId);
    if (!cp) return;
    showModal('Edit Check Point', `
        <div class="form-group"><label>Code</label><input id="ecp-code" value="${cp.code}"></div>
        <div class="form-group"><label>Name</label><input id="ecp-name" value="${cp.name}"></div>
        <div class="form-group"><label>Owner</label><input id="ecp-owner" value="${cp.owner}"></div>
        <div class="form-group"><label>Description</label><textarea id="ecp-desc" rows="2">${cp.description||''}</textarea></div>
        <div class="form-row">
            <div class="form-group"><label>Domain</label><select id="ecp-domain"><option value="">-</option><option ${cp.domain==='All'?'selected':''}>All</option><option ${cp.domain==='Shop'?'selected':''}>Shop</option><option ${cp.domain==='Buy'?'selected':''}>Buy</option><option ${cp.domain==='Own'?'selected':''}>Own</option><option ${cp.domain==='Parts'?'selected':''}>Parts</option></select></div>
            <div class="form-group"><label>Stream</label><select id="ecp-stream"><option value="">-</option><option ${cp.stream==='All'?'selected':''}>All</option><option ${cp.stream==='D2C'?'selected':''}>D2C</option><option ${cp.stream==='Channel Partner'?'selected':''}>Channel Partner</option><option ${cp.stream==='Platform Services'?'selected':''}>Platform Services</option></select></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>UOM</label><input id="ecp-uom" value="${cp.uom||''}"></div>
            <div class="form-group"><label>From</label><input id="ecp-from" value="${cp.target_from||''}"></div>
            <div class="form-group"><label>To</label><input id="ecp-to" value="${cp.target_to||''}"></div>
        </div>
        <div class="form-group"><label>Target Quarter</label><select id="ecp-quarter"><option value="">-</option><option ${cp.target_quarter==='Q1'?'selected':''}>Q1</option><option ${cp.target_quarter==='Q2'?'selected':''}>Q2</option><option ${cp.target_quarter==='Q3'?'selected':''}>Q3</option><option ${cp.target_quarter==='Q4'?'selected':''}>Q4</option></select></div>
        <div class="btn-group"><button class="btn btn-danger btn-sm" onclick="deleteCPConfirm('${cpId}')">Delete</button><div><button class="btn btn-secondary" onclick="closeModal()">Cancel</button> <button class="btn btn-primary" onclick="submitEditCP('${cpId}')">Save</button></div></div>
    `);
}

async function submitEditCP(cpId) {
    const body = {
        code: document.getElementById('ecp-code').value,
        name: document.getElementById('ecp-name').value,
        owner: document.getElementById('ecp-owner').value,
        description: document.getElementById('ecp-desc').value || null,
        domain: document.getElementById('ecp-domain').value || null,
        stream: document.getElementById('ecp-stream').value || null,
        uom: document.getElementById('ecp-uom').value || null,
        target_from: document.getElementById('ecp-from').value || null,
        target_to: document.getElementById('ecp-to').value || null,
        target_quarter: document.getElementById('ecp-quarter').value || null,
    };
    try {
        const resp = await fetch(`${MPCP_API}/cps/${cpId}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

async function deleteCPConfirm(cpId) {
    if (!confirm('Delete this Check Point? It must have 0 Projects.')) return;
    try {
        const resp = await fetch(`${MPCP_API}/cps/${cpId}`, { method: 'DELETE', headers: mpHeaders() });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}


// ============ CREATE PROJECT MODAL ============
function showCreateProjectModal(cpId) {
    showModal('Create Project', `
        <div class="form-group"><label>Name <span class="required">*</span></label><input id="proj-name" placeholder="Project name"></div>
        <div class="form-row">
            <div class="form-group"><label>Type</label><select id="proj-type"><option value="">-</option><option value="Fixed_Bid">Fixed Bid</option><option value="Special">Special</option><option value="Bug">Bug</option><option value="Enhancement">Enhancement</option></select></div>
            <div class="form-group"><label>Vendor</label><select id="proj-vendor"><option value="">-</option><option>Exathought</option><option>Deloitte</option><option>TVSD</option><option>Evontech</option><option>Autovyn</option></select></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Product Owner</label><select id="proj-po"><option value="">-</option><option>Ashish Thakur</option><option>Akshay Bhosle</option><option>Prakash Bharati</option><option>Avinash Kumar</option><option>Bibin</option><option>Sumitra Rathod</option></select></div>
            <div class="form-group"><label>BU <span class="required">*</span></label><select id="proj-bu"><option value="">-</option><option value="IND-2W">IND-2W</option><option value="3W/CMB">3W/CMB</option><option value="IB">IB</option></select></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Domain <span class="required">*</span></label><select id="proj-domain"><option value="">-</option><option>All</option><option>Shop</option><option>Buy</option><option>Own</option><option>Parts</option></select></div>
            <div class="form-group"><label>Stream <span class="required">*</span></label><select id="proj-stream"><option value="">-</option><option>All</option><option>D2C</option><option>Channel Partner</option><option>Platform Services</option></select></div>
        </div>
        <div class="form-group"><label>Description</label><textarea id="proj-desc" rows="2"></textarea></div>
        <div class="form-group"><label>TVSM Engg POC</label><input id="proj-engg-poc" placeholder="e.g., Rithik Kumar, Ashish T (comma-separated)"></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitCreateProject('${cpId}')">Create</button></div>
    `);
}

async function submitCreateProject(cpId) {
    const name = document.getElementById('proj-name').value;
    const bu = document.getElementById('proj-bu').value;
    const domain = document.getElementById('proj-domain').value;
    const stream = document.getElementById('proj-stream').value;
    if (!name) { showToastNotification('Name is required', 'warning'); return; }
    if (!bu) { showToastNotification('BU is required', 'warning'); return; }
    if (!domain) { showToastNotification('Domain is required', 'warning'); return; }
    if (!stream) { showToastNotification('Stream is required', 'warning'); return; }
    const body = {
        name,
        project_type: document.getElementById('proj-type').value || null,
        vendor: document.getElementById('proj-vendor').value || null,
        product_owner: document.getElementById('proj-po').value || null,
        engg_poc: document.getElementById('proj-engg-poc').value || null,
        bu: bu,
        domain: domain,
        stream: stream,
        description: document.getElementById('proj-desc').value || null,
    };
    body.lob = body.bu;
    try {
        const resp = await fetch(`${MPCP_API}/cps/${cpId}/projects`, { method: 'POST', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}


// ============ EDIT PROJECT MODAL ============
function showEditProjectModal(projectId) {
    const p = mpcp.currentProject;
    if (!p) return;
    showModal('Edit Project', `
        <div class="form-group"><label>Name</label><input id="eproj-name" value="${p.name}"></div>
        <div class="form-row">
            <div class="form-group"><label>Type</label><select id="eproj-type"><option value="">-</option><option value="Fixed_Bid" ${p.project_type==='Fixed_Bid'?'selected':''}>Fixed Bid</option><option value="Special" ${p.project_type==='Special'?'selected':''}>Special</option><option value="Bug" ${p.project_type==='Bug'?'selected':''}>Bug</option><option value="Enhancement" ${p.project_type==='Enhancement'?'selected':''}>Enhancement</option></select></div>
            <div class="form-group"><label>Vendor</label><select id="eproj-vendor"><option value="">-</option><option ${p.vendor==='Exathought'?'selected':''}>Exathought</option><option ${p.vendor==='Deloitte'?'selected':''}>Deloitte</option><option ${p.vendor==='TVSD'?'selected':''}>TVSD</option><option ${p.vendor==='Evontech'?'selected':''}>Evontech</option><option ${p.vendor==='Autovyn'?'selected':''}>Autovyn</option></select></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Product Owner</label><select id="eproj-po"><option value="">-</option><option ${p.product_owner==='Ashish Thakur'?'selected':''}>Ashish Thakur</option><option ${p.product_owner==='Akshay Bhosle'?'selected':''}>Akshay Bhosle</option><option ${p.product_owner==='Prakash Bharati'?'selected':''}>Prakash Bharati</option><option ${p.product_owner==='Avinash Kumar'?'selected':''}>Avinash Kumar</option><option ${p.product_owner==='Bibin'?'selected':''}>Bibin</option><option ${p.product_owner==='Sumitra Rathod'?'selected':''}>Sumitra Rathod</option></select></div>
            <div class="form-group"><label>BU</label><select id="eproj-bu"><option value="">-</option><option value="IND-2W" ${p.bu==='IND-2W'?'selected':''}>IND-2W</option><option value="3W/CMB" ${p.bu==='3W/CMB'?'selected':''}>3W/CMB</option><option value="IB" ${p.bu==='IB'?'selected':''}>IB</option></select></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Domain</label><select id="eproj-domain"><option value="">-</option><option ${p.domain==='All'?'selected':''}>All</option><option ${p.domain==='Shop'?'selected':''}>Shop</option><option ${p.domain==='Buy'?'selected':''}>Buy</option><option ${p.domain==='Own'?'selected':''}>Own</option><option ${p.domain==='Parts'?'selected':''}>Parts</option></select></div>
            <div class="form-group"><label>Stream</label><select id="eproj-stream"><option value="">-</option><option ${p.stream==='All'?'selected':''}>All</option><option ${p.stream==='D2C'?'selected':''}>D2C</option><option ${p.stream==='Channel Partner'?'selected':''}>Channel Partner</option><option ${p.stream==='Platform Services'?'selected':''}>Platform Services</option></select></div>
        </div>
        <div class="form-group"><label>Description</label><textarea id="eproj-desc" rows="2">${p.description||''}</textarea></div>
        <div class="form-group"><label>TVSM Engg POC</label><input id="eproj-engg-poc" value="${p.engg_poc||''}" placeholder="e.g., Rithik Kumar, Ashish T (comma-separated)"></div>
        <div class="btn-group"><button class="btn btn-danger btn-sm" onclick="deleteProjectConfirm('${projectId}')">Delete</button><div><button class="btn btn-secondary" onclick="closeModal()">Cancel</button> <button class="btn btn-primary" onclick="submitEditProject('${projectId}')">Save</button></div></div>
    `);
}

async function submitEditProject(projectId) {
    const body = {
        name: document.getElementById('eproj-name').value,
        project_type: document.getElementById('eproj-type').value || null,
        vendor: document.getElementById('eproj-vendor').value || null,
        product_owner: document.getElementById('eproj-po').value || null,
        engg_poc: document.getElementById('eproj-engg-poc').value || null,
        lob: document.getElementById('eproj-bu').value || null,
        domain: document.getElementById('eproj-domain').value || null,
        stream: document.getElementById('eproj-stream').value || null,
        description: document.getElementById('eproj-desc').value || null,
    };
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

async function deleteProjectConfirm(projectId) {
    if (!confirm('Delete this project and all its track data? This cannot be undone.')) return;
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}`, { method: 'DELETE', headers: mpHeaders() });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}


// ============ MOVE PROJECT (reassign parent MP/CP) ============
async function showMoveProjectModal(projectId) {
    try {
        const resp = await fetch(`${MPCP_API}/mps`, { headers: mpHeaders() });
        if (!resp.ok) throw new Error('Failed to load MPs');
        const mps = await resp.json();

        const currentCpId = (mpcp.currentProject && mpcp.currentProject.parent_cp_id) || '';
        let cpOptions = '';
        for (const mp of mps) {
            const cpsResp = await fetch(`${MPCP_API}/mps/${mp.id}/cps`, { headers: mpHeaders() });
            if (cpsResp.ok) {
                const cps = await cpsResp.json();
                for (const cp of cps) {
                    const sel = cp.id === currentCpId ? ' selected' : '';
                    cpOptions += `<option value="${cp.id}"${sel}>${mp.code} > ${cp.code} - ${cp.name}</option>`;
                }
            }
        }
        if (!cpOptions) {
            showToastNotification('No Check Points available to move to.', 'warning');
            return;
        }
        showModal('Move Project', `
            <p style="font-size:12px;color:#666;margin-bottom:10px;">Reassign this project to a different Managing Point / Check Point. All track data (process, milestones, dependencies, budget) moves with it.</p>
            <div class="form-group"><label>Target Check Point <span class="required">*</span></label>
                <select id="move-cp" style="width:100%">${cpOptions}</select>
            </div>
            <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitMoveProject('${projectId}')">Move</button></div>
        `);
    } catch (e) {
        showToastNotification(e.message, 'error');
    }
}

async function submitMoveProject(projectId) {
    const targetCpId = document.getElementById('move-cp').value;
    if (!targetCpId) { showToastNotification('Please select a target Check Point', 'warning'); return; }
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/move`, {
            method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify({ target_cp_id: targetCpId }),
        });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        showToastNotification('Project moved successfully', 'success');
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}


// ============ CREATE PROJECT PICKER (select CP first) ============
async function showCreateProjectPickerModal() {
    // Load all CPs to let user pick which one to add project under
    try {
        const resp = await fetch(`${MPCP_API}/mps`, { headers: mpHeaders() });
        if (!resp.ok) throw new Error('Failed to load MPs');
        const mps = await resp.json();

        // Build CP options grouped by MP
        let cpOptions = '';
        for (const mp of mps) {
            const cpsResp = await fetch(`${MPCP_API}/mps/${mp.id}/cps`, { headers: mpHeaders() });
            if (cpsResp.ok) {
                const cps = await cpsResp.json();
                for (const cp of cps) {
                    cpOptions += `<option value="${cp.id}">${mp.code} > ${cp.code} - ${cp.name}</option>`;
                }
            }
        }

        if (!cpOptions) {
            showToastNotification('No Check Points exist yet. Create MPs and CPs first, then add projects under them.', 'warning', 'Go to Managing Points', '#mpcp-tracker/mps');
            return;
        }

        showModal('Add Project — Select Check Point', `
            <div class="form-group"><label>Parent Check Point <span class="required">*</span></label>
                <select id="picker-cp" style="width:100%">${cpOptions}</select>
            </div>
            <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="proceedToCreateProject()">Next →</button></div>
        `);
    } catch (e) {
        showToastNotification(e.message, 'error');
    }
}

function proceedToCreateProject() {
    const cpId = document.getElementById('picker-cp').value;
    if (!cpId) { showToastNotification('Please select a Check Point', 'warning'); return; }
    closeModal();
    showCreateProjectModal(cpId);
}


// ============ SEND WEEKLY REPORT ============
async function sendWeeklyReport() {
    if (!confirm('Send the weekly MPCP report email now?')) return;
    try {
        const resp = await fetch(`${MPCP_API}/weekly-report`, { method: 'POST', headers: mpHeaders() });
        const result = await resp.json();
        if (result.success) {
            showToastNotification('Weekly report sent to: ' + result.recipients.join(', '), 'success');
        } else {
            showToastNotification(result.message, 'warning');
        }
    } catch (e) {
        showToastNotification(e.message, 'error');
    }
}


// ============ MPCP SETTINGS PAGE ============
let mpcp_config = null;

async function renderMPCPSettings(container) {
    container.innerHTML = '<div class="card"><p>Loading settings...</p></div>';
    try {
        const resp = await fetch(`${MPCP_API}/config`, { headers: mpHeaders() });
        if (!resp.ok) throw new Error('Failed to load config');
        mpcp_config = await resp.json();
    } catch (e) {
        container.innerHTML = `<div class="card"><p style="color:#c62828">Error: ${e.message}</p></div>`;
        return;
    }

    container.innerHTML = `
        <div class="card">
            <h2>⚙️ MPCP Tracker Settings</h2>
            <p class="subtitle">Manage configurable lists for Vendors, Product Owners, and Engineering Managers</p>

            <div style="margin-top:20px">
                <h3>Vendors</h3>
                <p style="font-size:12px;color:#666;margin-bottom:8px">These appear in project and milestone dropdowns</p>
                <div id="cfg-vendors" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px">
                    ${mpcp_config.vendors.map(v => `<span style="background:#e8eaf6;padding:4px 10px;border-radius:12px;font-size:12px;display:inline-flex;align-items:center;gap:4px">${v} <span onclick="removeConfigItem('vendors','${v}')" style="cursor:pointer;color:#c62828;font-weight:bold">×</span></span>`).join('')}
                </div>
                <div style="display:flex;gap:8px"><input id="new-vendor" placeholder="Add vendor..." style="flex:1;padding:6px 10px;border:1px solid #ddd;border-radius:6px;font-size:12px"><button class="btn btn-sm btn-primary" onclick="addConfigItem('vendors','new-vendor')">Add</button></div>
            </div>

            <div style="margin-top:20px">
                <h3>Product Owners</h3>
                <p style="font-size:12px;color:#666;margin-bottom:8px">These appear in project assignment dropdowns</p>
                <div id="cfg-pos" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px">
                    ${mpcp_config.product_owners.map(v => `<span style="background:#e8f5e9;padding:4px 10px;border-radius:12px;font-size:12px;display:inline-flex;align-items:center;gap:4px">${v} <span onclick="removeConfigItem('product_owners','${v}')" style="cursor:pointer;color:#c62828;font-weight:bold">×</span></span>`).join('')}
                </div>
                <div style="display:flex;gap:8px"><input id="new-po" placeholder="Add product owner..." style="flex:1;padding:6px 10px;border:1px solid #ddd;border-radius:6px;font-size:12px"><button class="btn btn-sm btn-primary" onclick="addConfigItem('product_owners','new-po')">Add</button></div>
            </div>

            <div style="margin-top:20px">
                <h3>Engineering Managers</h3>
                <p style="font-size:12px;color:#666;margin-bottom:8px">Engineering managers who can be assigned to projects</p>
                <div id="cfg-ems" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px">
                    ${(mpcp_config.engineering_managers||[]).map(v => `<span style="background:#fff3e0;padding:4px 10px;border-radius:12px;font-size:12px;display:inline-flex;align-items:center;gap:4px">${v} <span onclick="removeConfigItem('engineering_managers','${v}')" style="cursor:pointer;color:#c62828;font-weight:bold">×</span></span>`).join('')}
                    ${(mpcp_config.engineering_managers||[]).length === 0 ? '<span style="font-size:12px;color:#999">No EMs configured yet</span>' : ''}
                </div>
                <div style="display:flex;gap:8px"><input id="new-em" placeholder="Add engineering manager..." style="flex:1;padding:6px 10px;border:1px solid #ddd;border-radius:6px;font-size:12px"><button class="btn btn-sm btn-primary" onclick="addConfigItem('engineering_managers','new-em')">Add</button></div>
            </div>
        </div>
    `;
}

async function addConfigItem(listKey, inputId) {
    const input = document.getElementById(inputId);
    const value = input.value.trim();
    if (!value) return;
    if (!mpcp_config[listKey]) mpcp_config[listKey] = [];
    if (mpcp_config[listKey].includes(value)) { showToastNotification('Already exists', 'warning'); return; }
    mpcp_config[listKey].push(value);
    await saveConfig();
    input.value = '';
    refreshCurrentMPCPView();
}

async function removeConfigItem(listKey, value) {
    mpcp_config[listKey] = mpcp_config[listKey].filter(v => v !== value);
    await saveConfig();
    refreshCurrentMPCPView();
}

async function saveConfig() {
    try {
        const resp = await fetch(`${MPCP_API}/config`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(mpcp_config) });
        if (!resp.ok) throw new Error('Failed to save');
        showToastNotification('Settings saved', 'success');
    } catch (e) { showToastNotification(e.message, 'error'); }
}

// Load config for dropdowns (called when rendering create/edit modals)
async function loadMPCPConfig() {
    if (mpcp_config) return mpcp_config;
    try {
        const resp = await fetch(`${MPCP_API}/config`, { headers: mpHeaders() });
        if (resp.ok) mpcp_config = await resp.json();
    } catch (e) { /* use defaults */ }
    return mpcp_config || { vendors: [], product_owners: [], engineering_managers: [] };
}


// ============ EDIT/DELETE DEPENDENCY ============
function showEditDependencyModal(projectId, depId) {
    const dep = mpcp.dependencies.find(d => d.id === depId);
    if (!dep) { showToastNotification('Dependency not found', 'error'); return; }
    const milestones = mpcp.executionTrack?.milestones || [];
    const msOptions = milestones.map(m => `<option value="${m.id}" ${dep.milestone_id===m.id?'selected':''}>${m.name}</option>`).join('');
    showModal('Edit Dependency', `
        <div class="form-group"><label>Description</label><input id="edep-desc" value="${dep.description}"></div>
        <div class="form-group"><label>Owner</label><input id="edep-owner" value="${dep.external_owner}"></div>
        <div class="form-group"><label>ETA / Cutoff Date</label><input type="date" id="edep-cutoff" value="${dep.cutoff_date}"></div>
        <div class="form-group"><label>Status</label><select id="edep-status">
            <option value="Open" ${dep.status==='Open'?'selected':''}>Open</option>
            <option value="WIP" ${dep.status==='WIP'?'selected':''}>WIP</option>
            <option value="Resolved" ${dep.status==='Resolved'?'selected':''}>Resolved</option>
            <option value="Escalated" ${dep.status==='Escalated'?'selected':''}>Escalated</option>
        </select></div>
        <div class="form-group"><label>Linked Milestone</label><select id="edep-milestone"><option value="" ${!dep.milestone_id?'selected':''}>Project level</option>${msOptions}</select></div>
        <div class="form-group"><label>Escalation Note</label><input id="edep-escalation" value="${dep.escalation_note||''}" placeholder="If escalated, add note"></div>
        <div class="form-group"><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" id="edep-blocker" ${dep.is_blocker?'checked':''} style="width:auto;margin:0"> <span style="color:#c62828;font-weight:600">🚫 Mark as Blocker</span></label></div>
        <div class="btn-group"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitEditDependency('${projectId}','${depId}')">Save</button></div>
    `);
}

async function submitEditDependency(projectId, depId) {
    const body = {
        description: document.getElementById('edep-desc').value || null,
        external_owner: document.getElementById('edep-owner').value || null,
        cutoff_date: document.getElementById('edep-cutoff').value || null,
        status: document.getElementById('edep-status').value || null,
        milestone_id: document.getElementById('edep-milestone').value || null,
        escalation_note: document.getElementById('edep-escalation').value || null,
        is_blocker: document.getElementById('edep-blocker').checked,
    };
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/dependencies/${depId}`, { method: 'PUT', headers: mpHeadersJson(), body: JSON.stringify(body) });
        if (!resp.ok) { const e = await resp.json(); throw new Error(Array.isArray(e.detail) ? e.detail.map(d=>d.msg||d.error).join(', ') : e.detail || 'Failed'); }
        closeModal();
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}

async function deleteDependencyConfirm(projectId, depId) {
    if (!confirm('Delete this dependency?')) return;
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/dependencies/${depId}`, { method: 'DELETE', headers: mpHeaders() });
        if (!resp.ok) { const e = await resp.json(); throw new Error(e.detail || 'Failed'); }
        refreshCurrentMPCPView();
    } catch (e) { showToastNotification(e.message, 'error'); }
}


// ============ GANTT CHART (CSS-only timeline, dual-row planned vs actual) ============
function renderGanttChart(milestones) {
    const dated = milestones.filter(m => m.planned_start || m.actual_start);
    if (dated.length < 1) return '<p style="font-size:12px;color:#666;margin-bottom:12px;background:#fff8e1;padding:8px 12px;border-radius:6px;border-left:3px solid #f57f17">💡 Set <strong>Planned Start</strong> and <strong>Planned End</strong> on milestones (✏️) to see the Gantt timeline here.</p>';

    // Compute time range across milestones
    const allTimes = [];
    dated.forEach(m => {
        if (m.planned_start) allTimes.push(new Date(m.planned_start).getTime());
        if (m.planned_end) allTimes.push(new Date(m.planned_end).getTime());
        if (m.actual_start) allTimes.push(new Date(m.actual_start).getTime());
        if (m.actual_end) allTimes.push(new Date(m.actual_end).getTime());
    });
    // Also include tasks from _ganttTasksCache if available
    const tasksCache = window._ganttTasksCache || {};
    Object.values(tasksCache).forEach(tasks => {
        tasks.forEach(t => {
            if (t.planned_start) allTimes.push(new Date(t.planned_start).getTime());
            if (t.planned_end) allTimes.push(new Date(t.planned_end).getTime());
            if (t.actual_start) allTimes.push(new Date(t.actual_start).getTime());
            if (t.actual_end) allTimes.push(new Date(t.actual_end).getTime());
        });
    });

    let minTime = Math.min(...allTimes);
    let maxTime = Math.max(...allTimes);
    minTime -= 2 * 86400000;
    maxTime += 2 * 86400000;
    const minSpan = 14 * 86400000;
    if (maxTime - minTime < minSpan) maxTime = minTime + minSpan;
    const span = maxTime - minTime;

    const pos = (d) => ((new Date(d).getTime() - minTime) / span * 100);
    const barWidth = (startD, endD) => Math.max(((new Date(endD).getTime() - new Date(startD).getTime()) / span * 100), 0.5);

    // Generate week header labels (every Monday)
    const dayMs = 86400000;
    let weekHeaders = '';
    let gridlines = '';
    let dayTime = minTime;
    while (dayTime <= maxTime) {
        const p = ((dayTime - minTime) / span * 100);
        const d = new Date(dayTime);
        const isMonday = d.getDay() === 1;
        if (isMonday) {
            gridlines += `<div style="position:absolute;left:${p}%;top:0;bottom:0;border-left:1.5px solid #bbb;z-index:0"></div>`;
            const label = d.toLocaleDateString('en', {month:'short', day:'numeric'});
            weekHeaders += `<div style="position:absolute;left:${p}%;font-size:9px;color:#666;white-space:nowrap;transform:translateX(-50%)">${label}</div>`;
        } else {
            gridlines += `<div style="position:absolute;left:${p}%;top:0;bottom:0;border-left:1px solid #f0f0f0;z-index:0"></div>`;
        }
        dayTime += dayMs;
    }

    // Build rows — each item gets TWO distinct rows: one for Planned, one for Actual
    const barH = 10; // bar height in px
    const rowH = 16; // single row height (bar + padding)
    let rows = '';

    milestones.forEach(m => {
        const hasDates = m.planned_start || m.actual_start;

        if (!hasDates) {
            // Compact single row for milestones with no dates
            rows += `<div style="display:flex;align-items:center;height:24px;margin-bottom:2px;opacity:0.5">`;
            rows += `<div style="width:200px;flex-shrink:0;font-size:11px;color:#999;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${m.name}">○ ${m.name}</div>`;
            rows += `<div style="flex:1;position:relative;height:24px">${gridlines}<div style="position:absolute;top:6px;left:4px;font-size:9px;color:#ccc">—</div></div>`;
            rows += `</div>`;
            return;
        }

        // Milestone with dates — dual row (P + A)
        rows += `<div style="display:flex;align-items:start;margin-bottom:4px;border-bottom:1px solid #f0f0f0;padding-bottom:4px">`;
        rows += `<div style="width:200px;flex-shrink:0;font-size:11px;color:#1a237e;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:${barH * 2 + 2}px" title="${m.name}">● ${m.name}</div>`;
        rows += `<div style="flex:1;position:relative;height:${barH * 2 + 2}px">`;
        rows += gridlines;

        // Row 1: Planned bar
        if (m.planned_start && m.planned_end) {
            const left = pos(m.planned_start);
            const width = barWidth(m.planned_start, m.planned_end);
            rows += `<div style="position:absolute;left:${left}%;width:${width}%;height:${barH}px;background:#90CAF9;border-radius:3px;top:1px;z-index:1" title="Planned: ${m.planned_start} → ${m.planned_end}"></div>`;
        }

        // Row 2: Actual bar (directly below, no gap)
        if (m.actual_start) {
            const aEnd = m.actual_end || new Date().toISOString().slice(0, 10);
            const left = pos(m.actual_start);
            const width = barWidth(m.actual_start, aEnd);
            const color = m.is_delayed ? '#FF5252' : '#4caf50';
            rows += `<div style="position:absolute;left:${left}%;width:${width}%;height:${barH}px;background:${color};border-radius:3px;top:${barH + 1}px;z-index:1" title="Actual: ${m.actual_start} → ${m.actual_end || 'ongoing'}"></div>`;
        }

        rows += `</div></div>`;

        // Tasks under this milestone (from cache)
        const tasks = tasksCache[m.id] || [];
        tasks.forEach(t => {
            const taskHasDates = t.planned_start || t.actual_start;
            if (!taskHasDates) return;
            rows += `<div style="display:flex;align-items:start;margin-bottom:2px">`;
            rows += `<div style="width:200px;flex-shrink:0;font-size:10px;color:#555;padding-left:18px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:${barH * 2}px" title="${t.name}">└ ${t.name}</div>`;
            rows += `<div style="flex:1;position:relative;height:${barH * 2}px">`;
            rows += gridlines;

            // Task Planned bar (row 1)
            if (t.planned_start && t.planned_end) {
                const left = pos(t.planned_start);
                const width = barWidth(t.planned_start, t.planned_end);
                rows += `<div style="position:absolute;left:${left}%;width:${width}%;height:${barH - 2}px;background:#BBDEFB;border-radius:2px;top:1px;z-index:1" title="Planned: ${t.planned_start} → ${t.planned_end}"></div>`;
            }
            // Task Actual bar (row 2, no gap)
            if (t.actual_start) {
                const aEnd = t.actual_end || new Date().toISOString().slice(0, 10);
                const left = pos(t.actual_start);
                const width = barWidth(t.actual_start, aEnd);
                const isDelayed = t.actual_end && t.planned_end && new Date(t.actual_end) > new Date(t.planned_end);
                const color = isDelayed ? '#EF9A9A' : '#A5D6A7';
                rows += `<div style="position:absolute;left:${left}%;width:${width}%;height:${barH - 2}px;background:${color};border-radius:2px;top:${barH - 1}px;z-index:1" title="Actual: ${t.actual_start} → ${t.actual_end || 'ongoing'}"></div>`;
            }
            rows += `</div></div>`;
        });
    });

    return `<div style="background:#fafafa;border-radius:8px;padding:16px;margin-bottom:16px;overflow-x:auto">
        <div style="display:flex;gap:12px;margin-bottom:10px;font-size:10px">
            <span style="display:inline-flex;align-items:center;gap:3px"><span style="width:14px;height:8px;background:#90CAF9;border-radius:2px;display:inline-block"></span>Planned</span>
            <span style="display:inline-flex;align-items:center;gap:3px"><span style="width:14px;height:8px;background:#4caf50;border-radius:2px;display:inline-block"></span>Actual (On Track)</span>
            <span style="display:inline-flex;align-items:center;gap:3px"><span style="width:14px;height:8px;background:#FF5252;border-radius:2px;display:inline-block"></span>Actual (Delayed)</span>
        </div>
        <div style="display:flex;margin-bottom:8px">
            <div style="width:200px;flex-shrink:0"></div>
            <div style="flex:1;position:relative;height:16px">${weekHeaders}</div>
        </div>
        ${rows}
    </div>`;
}

// Load all tasks for Gantt rendering
async function loadGanttTasks(projectId) {
    try {
        const resp = await fetch(`${MPCP_API}/projects/${projectId}/all-tasks`, { headers: mpHeaders() });
        if (resp.ok) {
            window._ganttTasksCache = await resp.json();
        } else {
            window._ganttTasksCache = {};
        }
    } catch (e) {
        window._ganttTasksCache = {};
    }
}
