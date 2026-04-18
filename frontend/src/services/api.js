export const API_BASE = "http://localhost:8000";
export const WS_BASE = "ws://localhost:8000";
const TOKEN_KEY = "fraudguard_token";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const token = getStoredToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }

  return data;
}

export async function signup(payload) {
  return request("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getCurrentUser() {
  return request("/auth/me");
}

export async function logout() {
  return request("/auth/logout", { method: "POST" });
}

export async function getHealth() {
  return request("/health");
}

export async function getDashboardSummary() {
  return request("/dashboard/summary");
}

export async function getGraph() {
  return request("/graph-data");
}

export async function getClusters() {
  return request("/clusters");
}

export async function getTransactions({ risk = "all", device = "all", limit = 50 } = {}) {
  const params = new URLSearchParams({ risk, device, limit: String(limit) });
  return request(`/transactions?${params.toString()}`);
}

export async function predict(transaction) {
  return request("/predict", {
    method: "POST",
    body: JSON.stringify({ transaction }),
  });
}

export async function seedDemoTransactions(count = 8) {
  return request("/demo/seed", {
    method: "POST",
    body: JSON.stringify({ count }),
  });
}

export function createDashboardSocket({ onMessage, onOpen, onClose }) {
  const socket = new WebSocket(`${WS_BASE}/ws/dashboard`);

  socket.addEventListener("open", () => {
    if (onOpen) {
      onOpen();
    }
    socket.send("subscribe");
  });

  socket.addEventListener("message", (event) => {
    if (onMessage) {
      onMessage(JSON.parse(event.data));
    }
  });

  socket.addEventListener("close", () => {
    if (onClose) {
      onClose();
    }
  });

  return socket;
}
