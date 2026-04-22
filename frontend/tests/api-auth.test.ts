const apiInstance = {
  get: jest.fn(),
  post: jest.fn(),
  request: jest.fn(),
  interceptors: {
    response: {
      use: jest.fn(),
    },
  },
};

jest.mock("axios", () => ({
  __esModule: true,
  default: {
    create: jest.fn(() => apiInstance),
  },
}));

describe("API client and auth helpers", () => {
  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    apiInstance.get.mockReset();
    apiInstance.post.mockReset();
    apiInstance.request.mockReset();
    apiInstance.interceptors.response.use.mockReset();
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    document.cookie = "access=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    document.cookie = "refresh=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    window.history.pushState({}, "", "/dashboard");
  });

  it("creates an axios client and passes successful responses through", async () => {
    const { api } = await import("../src/lib/api");
    const [onFulfilled] = api.interceptors.response.use.mock.calls[0];

    const response = { data: { ok: true } };
    expect(onFulfilled(response)).toBe(response);
  });

  it("refreshes once on auth errors and retries the original request", async () => {
    const { api } = await import("../src/lib/api");
    const [, onRejected] = api.interceptors.response.use.mock.calls[0];
    const originalRequest = { url: "/private" };
    apiInstance.post.mockResolvedValueOnce({});
    apiInstance.request.mockResolvedValueOnce({ data: "retry" });

    await expect(
      onRejected({ response: { status: 401 }, config: originalRequest }),
    ).resolves.toEqual({ data: "retry" });
    expect(apiInstance.post).toHaveBeenCalledWith("/auth/refresh/");
    expect(apiInstance.request).toHaveBeenCalledWith({ url: "/private", _retry: true });
  });

  it("queues concurrent auth failures during refresh", async () => {
    const { api } = await import("../src/lib/api");
    const [, onRejected] = api.interceptors.response.use.mock.calls[0];
    let releaseRefresh!: () => void;
    apiInstance.post.mockReturnValueOnce(
      new Promise<void>((resolve) => {
        releaseRefresh = resolve;
      }),
    );
    apiInstance.request.mockResolvedValue({ data: "retried" });

    const first = onRejected({ response: { status: 403 }, config: { url: "/one" } });
    const second = onRejected({ response: { status: 401 }, config: { url: "/two" } });

    releaseRefresh();
    await expect(first).resolves.toEqual({ data: "retried" });
    await expect(second).resolves.toEqual({ data: "retried" });
    expect(apiInstance.request).toHaveBeenCalledWith({ url: "/two", _retry: true });
  });

  it("redirects to login when refresh fails and ignores login/register auth errors", async () => {
    const { api } = await import("../src/lib/api");
    const [, onRejected] = api.interceptors.response.use.mock.calls[0];
    const refreshError = new Error("refresh failed");
    apiInstance.post.mockRejectedValueOnce(refreshError);
    const consoleError = jest.spyOn(console, "error").mockImplementation(() => {});

    await expect(
      onRejected({ response: { status: 401 }, config: { url: "/private" } }),
    ).rejects.toBe(refreshError);
    expect(consoleError).toHaveBeenCalled();
    consoleError.mockRestore();

    await expect(
      onRejected({ response: { status: 401 }, config: { url: "/auth/login" } }),
    ).rejects.toEqual({ response: { status: 401 }, config: { url: "/auth/login" } });

    await expect(
      onRejected({ response: { status: 403 }, config: { url: "/auth/register" } }),
    ).rejects.toEqual({ response: { status: 403 }, config: { url: "/auth/register" } });
  });

  it("passes through non-auth and already-retried errors", async () => {
    const { api } = await import("../src/lib/api");
    const [, onRejected] = api.interceptors.response.use.mock.calls[0];
    const serverError = { response: { status: 500 }, config: { url: "/private" } };
    const retriedError = { response: { status: 401 }, config: { url: "/private", _retry: true } };

    await expect(onRejected(serverError)).rejects.toEqual(serverError);
    await expect(onRejected(retriedError)).rejects.toEqual(retriedError);
  });

  it("checks the session on focus and visible-state events when auth cookies exist", async () => {
    document.cookie = "access=token; path=/";
    const { api } = await import("../src/lib/api");
    apiInstance.get.mockResolvedValue({});

    apiInstance.get.mockClear();
    window.dispatchEvent(new Event("focus"));
    await Promise.resolve();
    expect(api.get).toHaveBeenCalledWith("/auth/me/");

    const callsAfterFocus = api.get.mock.calls.length;
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    document.dispatchEvent(new Event("visibilitychange"));
    await Promise.resolve();
    expect(api.get.mock.calls.length).toBeGreaterThan(callsAfterFocus);
  });

  it("does not check the session on login pages or without auth cookies", async () => {
    let focusHandler: (() => Promise<void>) | undefined;
    const addWindowListener = jest
      .spyOn(window, "addEventListener")
      .mockImplementation((event, handler) => {
        if (event === "focus") {
          focusHandler = handler as () => Promise<void>;
        }
      });

    const { api } = await import("../src/lib/api");
    apiInstance.get.mockResolvedValue({});

    apiInstance.get.mockClear();
    await focusHandler?.();
    expect(api.get).not.toHaveBeenCalled();

    window.history.pushState({}, "", "/login");
    document.cookie = "refresh=token; path=/";
    await focusHandler?.();
    expect(api.get).not.toHaveBeenCalled();
    addWindowListener.mockRestore();
  });

  it("ignores hidden visibility changes and swallowed session-check failures", async () => {
    document.cookie = "access=token; path=/";
    const { api } = await import("../src/lib/api");
    apiInstance.get.mockRejectedValueOnce(new Error("expired"));

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "hidden",
    });
    document.dispatchEvent(new Event("visibilitychange"));
    await Promise.resolve();
    expect(api.get).not.toHaveBeenCalled();

    window.dispatchEvent(new Event("focus"));
    await Promise.resolve();
    expect(api.get).toHaveBeenCalledWith("/auth/me/");
  });

  it("reads csrf tokens from cookies after pinging the backend", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true }) as jest.Mock;
    document.cookie = "csrftoken=abc%20123; path=/";

    const { getCsrfToken } = await import("../src/lib/auth");
    await expect(getCsrfToken()).resolves.toBe("abc 123");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/auth/me/",
      { credentials: "include" },
    );

    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    await expect(getCsrfToken()).resolves.toBe("");
  });
});
