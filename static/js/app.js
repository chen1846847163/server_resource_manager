const API = "";

async function api(path, opts = {}) {
    const res = await fetch(API + path, {
        headers: { "Content-Type": "application/json", ...opts.headers },
        ...opts,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || res.statusText);
    }
    return res.json();
}

function statusBadge(status) {
    const cls = "status-" + status;
    const labels = { pending: "待执行", running: "执行中", completed: "已完成", failed: "失败", cancelled: "已取消", online: "在线", offline: "离线" };
    return `<span class="status-badge ${cls}">${labels[status] || status}</span>`;
}

function esc(s) {
    if (s == null) return "";
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// Dashboard
async function loadDashboard() {
    try {
        const d = await api("/api/dashboard/");
        document.getElementById("stat-total-servers").textContent = d.servers.total;
        document.getElementById("stat-online-servers").textContent = d.servers.online;
        document.getElementById("stat-disabled-servers").textContent = d.servers.disabled;
        document.getElementById("stat-test-cases").textContent = d.test_cases;
        document.getElementById("stat-pending").textContent = d.tasks.pending;
        document.getElementById("stat-running").textContent = d.tasks.running;
        document.getElementById("stat-completed").textContent = d.tasks.completed;
        document.getElementById("stat-failed").textContent = d.tasks.failed;

        const tasks = await api("/api/tasks/");
        const tbody = document.querySelector("#recent-tasks-table tbody");
        tbody.innerHTML = tasks.slice(0, 10).map(t => `
            <tr>
                <td>${t.id}</td>
                <td>${esc(t.name)}</td>
                <td>${statusBadge(t.status)}</td>
                <td>${esc(t.server_name || "-")}</td>
                <td>${t.created_at || "-"}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

// Servers
async function loadServers() {
    try {
        const servers = await api("/api/servers/");
        const tbody = document.querySelector("#servers-table tbody");
        tbody.innerHTML = servers.map(s => `
            <tr>
                <td>${s.id}</td>
                <td>${esc(s.name)}</td>
                <td>${esc(s.host)}</td>
                <td>${s.port}</td>
                <td>${statusBadge(s.status)}</td>
                <td>${s.enabled ? '<span class="status-badge status-online">启用</span>' : '<span class="status-badge status-offline">禁用</span>'}</td>
                <td>${esc(s.tags)}</td>
                <td class="actions-cell">
                    <button class="btn btn-sm ${s.enabled ? 'btn-warning' : 'btn-success'}" onclick="toggleServer(${s.id})">${s.enabled ? '禁用' : '启用'}</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteServer(${s.id})">删除</button>
                </td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Load servers error:", e);
    }
}

function showAddServerForm() { document.getElementById("add-server-form").style.display = "block"; }
function hideAddServerForm() { document.getElementById("add-server-form").style.display = "none"; }

async function addServer() {
    const name = document.getElementById("server-name").value.trim();
    const host = document.getElementById("server-host").value.trim();
    const port = parseInt(document.getElementById("server-port").value) || 22;
    const tags = document.getElementById("server-tags").value.trim();
    if (!name || !host) return alert("请填写名称和主机地址");
    await api("/api/servers/", { method: "POST", body: JSON.stringify({ name, host, port, tags }) });
    hideAddServerForm();
    loadServers();
}

async function toggleServer(id) {
    await api(`/api/servers/${id}/toggle`, { method: "POST" });
    loadServers();
}

async function deleteServer(id) {
    if (!confirm("确定删除该服务器?")) return;
    await api(`/api/servers/${id}`, { method: "DELETE" });
    loadServers();
}

// Test Cases
async function loadTestCases() {
    try {
        const cases = await api("/api/test-cases/");
        const tbody = document.querySelector("#cases-table tbody");
        tbody.innerHTML = cases.map(c => `
            <tr>
                <td>${c.id}</td>
                <td>${esc(c.name)}</td>
                <td>${esc(c.module)}</td>
                <td>${esc(c.description)}</td>
                <td>${c.created_at || "-"}</td>
                <td><button class="btn btn-sm btn-danger" onclick="deleteCase(${c.id})">删除</button></td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Load cases error:", e);
    }
}

function showImportForm() { document.getElementById("import-form").style.display = "block"; }
function hideImportForm() { document.getElementById("import-form").style.display = "none"; }
function showAddCaseForm() { document.getElementById("add-case-form").style.display = "block"; }
function hideAddCaseForm() { document.getElementById("add-case-form").style.display = "none"; }

async function importMockCases() {
    await api("/api/test-cases/import-mock", { method: "POST" });
    loadTestCases();
}

async function importCases() {
    const text = document.getElementById("import-json").value.trim();
    if (!text) return alert("请输入 JSON");
    const data = JSON.parse(text);
    await api("/api/test-cases/import", { method: "POST", body: JSON.stringify(data) });
    hideImportForm();
    loadTestCases();
}

async function addCase() {
    const name = document.getElementById("case-name").value.trim();
    const module_ = document.getElementById("case-module").value.trim();
    const desc = document.getElementById("case-desc").value.trim();
    if (!name) return alert("请填写用例名称");
    await api("/api/test-cases/", { method: "POST", body: JSON.stringify({ name, module: module_, description: desc }) });
    hideAddCaseForm();
    loadTestCases();
}

async function deleteCase(id) {
    if (!confirm("确定删除该用例?")) return;
    await api(`/api/test-cases/${id}`, { method: "DELETE" });
    loadTestCases();
}

// Tasks
let allCases = [];

async function loadCasesForSelector() {
    try {
        allCases = await api("/api/test-cases/");
    } catch (e) { console.error(e); }
}

async function loadTasks() {
    try {
        const tasks = await api("/api/tasks/");
        const tbody = document.querySelector("#tasks-table tbody");
        tbody.innerHTML = tasks.map(t => {
            const caseCount = Array.isArray(t.test_case_ids) ? t.test_case_ids.length : 0;
            let actions = `<button class="btn btn-sm btn-secondary" onclick="viewResult(${t.id})">查看</button>`;
            if (t.status === "pending" || t.status === "running") {
                actions += ` <button class="btn btn-sm btn-warning" onclick="cancelTask(${t.id})">取消</button>`;
            }
            actions += ` <button class="btn btn-sm btn-danger" onclick="deleteTask(${t.id})">删除</button>`;
            return `
                <tr>
                    <td>${t.id}</td>
                    <td>${esc(t.name)}</td>
                    <td>${statusBadge(t.status)}</td>
                    <td>${esc(t.server_name || "自动分配")}</td>
                    <td>${caseCount}</td>
                    <td>${t.created_at || "-"}</td>
                    <td>${t.finished_at || "-"}</td>
                    <td class="actions-cell">${actions}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error("Load tasks error:", e);
    }
}

function showCreateTaskForm() {
    const container = document.getElementById("case-checkboxes");
    container.innerHTML = allCases.map(c =>
        `<div class="case-checkbox"><label><input type="checkbox" value="${c.id}"> ${esc(c.name)} (${esc(c.module)})</label></div>`
    ).join("");
    document.getElementById("create-task-form").style.display = "block";
}
function hideCreateTaskForm() { document.getElementById("create-task-form").style.display = "none"; }

async function createTask() {
    const name = document.getElementById("task-name").value.trim();
    if (!name) return alert("请填写任务名称");
    const checkboxes = document.querySelectorAll("#case-checkboxes input:checked");
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));
    if (ids.length === 0) return alert("请至少选择一个测试用例");
    await api("/api/tasks/", { method: "POST", body: JSON.stringify({ name, test_case_ids: ids }) });
    hideCreateTaskForm();
    loadTasks();
}

async function cancelTask(id) {
    if (!confirm("确定取消该任务?")) return;
    await api(`/api/tasks/${id}/cancel`, { method: "POST" });
    loadTasks();
}

async function deleteTask(id) {
    if (!confirm("确定删除该任务?")) return;
    await api(`/api/tasks/${id}`, { method: "DELETE" });
    loadTasks();
}

async function viewResult(id) {
    try {
        const task = await api(`/api/tasks/${id}`);
        const body = document.getElementById("task-result-body");
        if (!task.result) {
            body.innerHTML = `<p style="color:var(--text-secondary)">暂无结果 (状态: ${task.status})</p>`;
        } else {
            const r = typeof task.result === "string" ? JSON.parse(task.result) : task.result;
            let html = `<div class="result-summary">
                <div class="stat"><div class="num">${r.summary.total}</div><div class="lbl">总计</div></div>
                <div class="stat"><div class="num" style="color:var(--success)">${r.summary.passed}</div><div class="lbl">通过</div></div>
                <div class="stat"><div class="num" style="color:var(--danger)">${r.summary.failed}</div><div class="lbl">失败</div></div>
            </div>`;
            if (r.details) {
                html += r.details.map(d => `
                    <div class="result-detail ${d.passed ? 'pass' : 'fail'}">
                        <strong>${esc(d.test_case)}</strong> on ${esc(d.server)}<br>
                        状态: ${d.passed ? '<span style="color:var(--success)">通过</span>' : '<span style="color:var(--danger)">失败</span>'}
                        | 耗时: ${d.duration_ms}ms
                        ${d.error ? '<br>错误: <span style="color:var(--danger)">' + esc(d.error) + '</span>' : ''}
                        <br><small style="color:var(--text-secondary)">${esc(d.output)}</small>
                    </div>
                `).join("");
            }
            body.innerHTML = html;
        }
        document.getElementById("task-result-modal").style.display = "flex";
    } catch (e) {
        alert("Error: " + e.message);
    }
}

function closeResultModal() {
    document.getElementById("task-result-modal").style.display = "none";
}
