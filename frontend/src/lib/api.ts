import axios, { AxiosInstance } from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const api: AxiosInstance = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── redirect helper ────────────────────────────────────────────────
function redirectToLogin() {
  if (
    globalThis.window !== undefined &&
    !globalThis.window.location.pathname.startsWith("/login")
  ) {
    globalThis.window.location.href = "/login";
  }
}

// ── response interceptor ───────────────────────────────────────────
let isRefreshing = false;
let refreshQueue: Array<() => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status;
    const originalRequest = error.config;

    // Do not attempt refresh for login/register requests
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

        // retry queued requests
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

// ── session check when user returns to tab ─────────────────────────
if (globalThis.window !== undefined) {
  const checkSessionOnFocus = async () => {
    // Skip on login page
    if (globalThis.window.location.pathname === "/login") return;

    // Only check session if cookies exist
    const hasAuthCookie =
      document.cookie.includes("access") || document.cookie.includes("refresh");

    if (!hasAuthCookie) return;

    try {
      await api.get("/auth/me/");
    } catch {
      // interceptor handles redirect
    }
  };

  // when tab becomes active
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      checkSessionOnFocus();
    }
  });

  // when window regains focus
  globalThis.window.addEventListener("focus", checkSessionOnFocus);
}
