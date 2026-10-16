// 本地開發：走 Vite proxy（空字串），正式環境用 VITE_API_URL
const API_BASE = import.meta.env.VITE_API_URL ?? "";

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    const msg = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((d) => d.msg || JSON.stringify(d)).join(", ")
        : data.message || `請求失敗 (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

export const api = {
  register: (body) => request("/api/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body) => request("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: () => request("/api/auth/me"),

  listPools: () => request("/api/pools"),
  getPool: (id) => request(`/api/pools/${id}`),

  draw: (body) => request("/api/draw", { method: "POST", body: JSON.stringify(body) }),

  myDrawRecords: () => request("/api/my/draw-records"),
  myTransactions: () => request("/api/my/transactions"),
  recharge: (body) => request("/api/recharge", { method: "POST", body: JSON.stringify(body) }),

  adminCreatePool: (formData) => request("/api/admin/pools", { method: "POST", body: formData }),
  adminUpdatePool: (id, formData) => request(`/api/admin/pools/${id}`, { method: "PUT", body: formData }),
  adminAddCard: (poolId, formData) => request(`/api/admin/pools/${poolId}/cards`, { method: "POST", body: formData }),
  adminListCards: (poolId) => request(`/api/admin/pools/${poolId}/cards`),
  adminRecharge: (body) => request("/api/admin/recharge", { method: "POST", body: JSON.stringify(body) }),
  adminTestRecharge: (body) => request("/api/admin/test-recharge", { method: "POST", body: JSON.stringify(body) }),
  adminUsers: () => request("/api/admin/users"),
  adminTransactions: (userId) => request(userId ? `/api/admin/transactions?user_id=${userId}` : "/api/admin/transactions"),
  adminDrawRecords: () => request("/api/admin/draw-records"),
  listAllPools: () => request("/api/pools?active_only=false"),
};

export default api;

// 圖片網址：雲端（Supabase）存的是完整 https 網址；本地則是 /uploads/xxx，需要加上後端網址
export function imgUrl(url) {
  if (!url) return "";
  if (/^https?:\/\//.test(url)) return url;
  return `${API_BASE}${url}`;
}
