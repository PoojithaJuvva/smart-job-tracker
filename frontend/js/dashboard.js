const STATUSES = ["Wishlist", "Applied", "OA_Scheduled", "Interview", "Offer", "Rejected", "Withdrawn"];
const STATUS_LABELS = {
  Wishlist: "Wishlist",
  Applied: "Applied",
  OA_Scheduled: "Online Assessment",
  Interview: "Interview",
  Offer: "Offer",
  Rejected: "Rejected",
  Withdrawn: "Withdrawn",
};

let state = {
  view: "overview",
  page: 1,
  perPage: 8,
  search: "",
  statusFilter: "",
  editingId: null,
};

document.addEventListener("DOMContentLoaded", async () => {
  if (!TokenStore.getAccess()) {
    window.location.href = "index.html";
    return;
  }

  populateStatusOptions();
  wireNav();
  wireModal();
  wireLogout();
  wireListControls();
  document.getElementById("export-csv-btn").addEventListener("click", exportCsv);

  const cachedUser = TokenStore.getUser();
  if (cachedUser) document.getElementById("user-name").textContent = cachedUser.name;
  try {
    const me = await Api.me();
    document.getElementById("user-name").textContent = me.name;
  } catch (_) { /* cached name already shown */ }

  await refreshOverview();
});

function populateStatusOptions() {
  const selects = [document.getElementById("field-status"), document.getElementById("status-filter")];
  selects.forEach((select) => {
    STATUSES.forEach((status) => {
      if (select.id === "status-filter" && status === "") return;
      const opt = document.createElement("option");
      opt.value = status;
      opt.textContent = STATUS_LABELS[status];
      select.appendChild(opt);
    });
  });
}

function wireNav() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });
}

async function switchView(view) {
  state.view = view;
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  document.getElementById(`view-${view}`).classList.remove("hidden");

  if (view === "overview") await refreshOverview();
  if (view === "board") await refreshBoard();
  if (view === "list") await refreshList();
}

function wireLogout() {
  document.getElementById("logout-btn").addEventListener("click", () => {
    TokenStore.clear();
    window.location.href = "index.html";
  });
}

/* ---------------- Overview ---------------- */

async function refreshOverview() {
  const summary = await Api.analyticsSummary();
  document.getElementById("stat-total").textContent = summary.total_applications;
  document.getElementById("stat-response").textContent = `${summary.response_rate_percent}%`;
  document.getElementById("stat-offer").textContent = `${summary.offer_rate_percent}%`;
  document.getElementById("stat-interviews").textContent = summary.upcoming_interviews.length;

  const breakdownEl = document.getElementById("status-breakdown");
  breakdownEl.innerHTML = "";
  STATUSES.forEach((status) => {
    const count = summary.by_status[status] || 0;
    const pill = document.createElement("span");
    pill.className = `status-pill status-${status}`;
    pill.textContent = `${STATUS_LABELS[status]} · ${count}`;
    breakdownEl.appendChild(pill);
  });

  const upcomingEl = document.getElementById("upcoming-list");
  upcomingEl.innerHTML = "";
  if (summary.upcoming_interviews.length === 0) {
    upcomingEl.innerHTML = `<li class="empty">Nothing scheduled yet.</li>`;
  } else {
    summary.upcoming_interviews.forEach((app) => {
      const li = document.createElement("li");
      const when = new Date(app.interview_date).toLocaleString();
      li.innerHTML = `<span>${escapeHtml(app.company)} — ${escapeHtml(app.role)}</span><span>${when}</span>`;
      upcomingEl.appendChild(li);
    });
  }

  [1, 2, 3].forEach((n) => {
    const el = document.getElementById(`open-add-modal-${n}`);
    if (el) el.onclick = () => openModal();
  });
}

/* ---------------- Board ---------------- */

async function refreshBoard() {
  const board = document.getElementById("board");
  board.innerHTML = "<p>Loading…</p>";

  const columns = {};
  STATUSES.forEach((s) => (columns[s] = []));

  let page = 1;
  let totalPages = 1;
  do {
    const res = await Api.listApplications({ page, per_page: 50 });
    res.items.forEach((app) => columns[app.status]?.push(app));
    totalPages = res.total_pages || 1;
    page += 1;
  } while (page <= totalPages);

  board.innerHTML = "";
  STATUSES.forEach((status) => {
    const col = document.createElement("div");
    col.className = "board-column";
    col.innerHTML = `<div class="board-column-title"><span>${STATUS_LABELS[status]}</span><span>${columns[status].length}</span></div>`;
    columns[status].forEach((app) => {
      const card = document.createElement("div");
      card.className = "board-card";
      card.innerHTML = `<div class="card-company">${escapeHtml(app.company)}</div><div class="card-role">${escapeHtml(app.role)}</div>`;
      card.addEventListener("click", () => openModal(app));
      col.appendChild(card);
    });
    board.appendChild(col);
  });
}

/* ---------------- List ---------------- */

function wireListControls() {
  const searchInput = document.getElementById("search-input");
  const statusFilter = document.getElementById("status-filter");
  let debounceTimer;

  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      state.search = searchInput.value.trim();
      state.page = 1;
      refreshList();
    }, 300);
  });

  statusFilter.addEventListener("change", () => {
    state.statusFilter = statusFilter.value;
    state.page = 1;
    refreshList();
  });
}

async function refreshList() {
  const tbody = document.getElementById("app-table-body");
  tbody.innerHTML = `<tr><td colspan="6">Loading…</td></tr>`;

  const res = await Api.listApplications({
    page: state.page,
    per_page: state.perPage,
    q: state.search,
    status: state.statusFilter,
  });

  tbody.innerHTML = "";
  if (res.items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6">No applications match yet — add one to get started.</td></tr>`;
  }
  res.items.forEach((app) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(app.company)}</td>
      <td>${escapeHtml(app.role)}</td>
      <td><span class="status-pill status-${app.status}">${STATUS_LABELS[app.status]}</span></td>
      <td>${app.applied_date || "—"}</td>
      <td>${escapeHtml(app.location || "—")}</td>
      <td>Edit</td>
    `;
    tr.addEventListener("click", () => openModal(app));
    tbody.appendChild(tr);
  });

  renderPagination(res);
}

function renderPagination(res) {
  const container = document.getElementById("pagination");
  container.innerHTML = "";
  for (let i = 1; i <= res.total_pages; i++) {
    const btn = document.createElement("button");
    btn.textContent = i;
    if (i === res.page) btn.classList.add("active");
    btn.addEventListener("click", () => {
      state.page = i;
      refreshList();
    });
    container.appendChild(btn);
  }
}

async function exportCsv() {
  try {
    const blob = await Api.exportCsv();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "job_applications.csv";
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    showToast("Export failed. Please try again.");
  }
}

/* ---------------- Modal (create/edit/delete) ---------------- */

function wireModal() {
  const modal = document.getElementById("app-modal");
  const form = document.getElementById("app-form");

  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("cancel-modal-btn").addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      company: document.getElementById("field-company").value.trim(),
      role: document.getElementById("field-role").value.trim(),
      status: document.getElementById("field-status").value,
      location: document.getElementById("field-location").value.trim() || null,
      salary_range: document.getElementById("field-salary").value.trim() || null,
      job_link: document.getElementById("field-job-link").value.trim() || null,
      notes: document.getElementById("field-notes").value.trim() || null,
      applied_date: document.getElementById("field-applied-date").value || null,
      interview_date: document.getElementById("field-interview-date").value || null,
    };

    try {
      if (state.editingId) {
        await Api.updateApplication(state.editingId, payload);
        showToast("Application updated.");
      } else {
        await Api.createApplication(payload);
        showToast("Application added.");
      }
      closeModal();
      await refreshCurrentView();
    } catch (err) {
      showToast(err.message || "Something went wrong.");
    }
  });

  document.getElementById("delete-app-btn").addEventListener("click", async () => {
    if (!state.editingId) return;
    if (!confirm("Delete this application? This cannot be undone.")) return;
    try {
      await Api.deleteApplication(state.editingId);
      showToast("Application deleted.");
      closeModal();
      await refreshCurrentView();
    } catch (err) {
      showToast(err.message || "Delete failed.");
    }
  });
}

function openModal(app = null) {
  state.editingId = app ? app.id : null;
  document.getElementById("modal-title").textContent = app ? "Edit Application" : "New Application";
  document.getElementById("delete-app-btn").classList.toggle("hidden", !app);

  document.getElementById("field-company").value = app?.company || "";
  document.getElementById("field-role").value = app?.role || "";
  document.getElementById("field-status").value = app?.status || "Applied";
  document.getElementById("field-location").value = app?.location || "";
  document.getElementById("field-salary").value = app?.salary_range || "";
  document.getElementById("field-job-link").value = app?.job_link || "";
  document.getElementById("field-notes").value = app?.notes || "";
  document.getElementById("field-applied-date").value = app?.applied_date || "";
  document.getElementById("field-interview-date").value = app?.interview_date ? app.interview_date.slice(0, 16) : "";

  document.getElementById("app-modal").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("app-modal").classList.add("hidden");
  document.getElementById("app-form").reset();
  state.editingId = null;
}

async function refreshCurrentView() {
  if (state.view === "overview") await refreshOverview();
  if (state.view === "board") await refreshBoard();
  if (state.view === "list") await refreshList();
}

/* ---------------- Utilities ---------------- */

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 2500);
}

function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
