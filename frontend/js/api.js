// Base URL of the Flask backend. Override by setting window.API_BASE before this
// script loads (e.g. in production, point it at your deployed API domain).
const API_BASE = window.API_BASE || "http://localhost:5000/api";

const TokenStore = {
  getAccess: () => localStorage.getItem("jt_access_token"),
  getRefresh: () => localStorage.getItem("jt_refresh_token"),
  set: (access, refresh) => {
    localStorage.setItem("jt_access_token", access);
    if (refresh) localStorage.setItem("jt_refresh_token", refresh);
  },
  clear: () => {
    localStorage.removeItem("jt_access_token");
    localStorage.removeItem("jt_refresh_token");
    localStorage.removeItem("jt_user");
  },
  setUser: (user) => localStorage.setItem("jt_user", JSON.stringify(user)),
  getUser: () => {
    const raw = localStorage.getItem("jt_user");
    return raw ? JSON.parse(raw) : null;
  },
};

async function apiRequest(path, { method = "GET", body, auth = true, isRetry = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = TokenStore.getAccess();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Access token expired — try a silent refresh once, then retry the request.
  if (response.status === 401 && auth && !isRetry && TokenStore.getRefresh()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return apiRequest(path, { method, body, auth, isRetry: true });
    }
    TokenStore.clear();
    window.location.href = "index.html";
    return Promise.reject(new Error("Session expired"));
  }

  let data = null;
  const text = await response.text();
  if (text) {
    try { data = JSON.parse(text); } catch (_) { data = text; }
  }

  if (!response.ok) {
    const message = (data && (data.error || JSON.stringify(data.errors))) || "Request failed";
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

async function tryRefreshToken() {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { Authorization: `Bearer ${TokenStore.getRefresh()}` },
    });
    if (!res.ok) return false;
    const data = await res.json();
    TokenStore.set(data.access_token, null);
    return true;
  } catch (_) {
    return false;
  }
}

async function apiGetBlob(path) {
  const token = TokenStore.getAccess();
  const response = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error("Export failed");
  return response.blob();
}

const Api = {
  register: (payload) => apiRequest("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) => apiRequest("/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => apiRequest("/auth/me"),

  listApplications: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== "" && v != null));
    return apiRequest(`/applications?${qs.toString()}`);
  },
  createApplication: (payload) => apiRequest("/applications", { method: "POST", body: payload }),
  getApplication: (id) => apiRequest(`/applications/${id}`),
  updateApplication: (id, payload) => apiRequest(`/applications/${id}`, { method: "PUT", body: payload }),
  deleteApplication: (id) => apiRequest(`/applications/${id}`, { method: "DELETE" }),
  analyticsSummary: () => apiRequest("/applications/analytics/summary"),
  exportCsv: () => apiGetBlob("/applications/export/csv"),
};
