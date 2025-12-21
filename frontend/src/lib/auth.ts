// src/lib/auth.ts
export const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function getToken() {
  return localStorage.getItem("themis:token");
}
export function saveAuth(token: string, user?: unknown) {
  localStorage.setItem("themis:token", token);
  if (user) localStorage.setItem("themis:user", JSON.stringify(user));
}
export function clearAuth() {
  localStorage.removeItem("themis:token");
  localStorage.removeItem("themis:user");
}
