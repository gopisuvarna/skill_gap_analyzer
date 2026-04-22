import axios, { AxiosInstance } from "axios";
import { getCsrfToken } from "./auth";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const api: AxiosInstance = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(async (config) => {
  const method = config.method?.toLowerCase();
  if (method && ["post", "put", "patch", "delete"].includes(method)) {
    const csrfToken = await getCsrfToken();
    if (csrfToken) {
      config.headers = config.headers ?? {};
      config.headers["X-CSRFToken"] = csrfToken;
    }
  }
  return config;
});

function redirectToLogin() {
  if (
    globalThis.window !== undefined &&
    !globalThis.window.location.pathname.startsWith("/login")
  ) {
    globalThis.window.location.href = "/login";
  }
}
let isRefreshing = false;
let refreshQueue: Array<() => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status;
    const originalRequest = error.config;
    if (
      (status === 401 || status === 403) &&
      !originalRequest?._retry &&
      !originalRequest.url?.includes("/auth/login") &&
      !originalRequest.url?.includes("/auth/register")
    ) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push(() =>
            resolve(api.request({ ...originalRequest, _retry: true })),
          );
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await api.post("/auth/refresh/");
        refreshQueue.forEach((cb) => cb());
        refreshQueue = [];

        return api.request(originalRequest);
      } catch (refreshError) {
        refreshQueue = [];
        redirectToLogin();
        throw refreshError;
      } finally {
        isRefreshing = false;
      }
    }

    throw error;
  },
);
if (globalThis.window !== undefined) {
  const checkSessionOnFocus = async () => {
    if (globalThis.window.location.pathname === "/login") return;
    const hasAuthCookie =
      document.cookie.includes("access") || document.cookie.includes("refresh");

    if (!hasAuthCookie) return;

    try {
      await api.get("/auth/me/");
    } catch {
    }
  };
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      checkSessionOnFocus();
    }
  });
  globalThis.window.addEventListener("focus", checkSessionOnFocus);
}
