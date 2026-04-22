import React from "react";
import { act, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";

const mockPush = jest.fn();
let mockPathname = "/dashboard";

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

const mockApi = jest.requireMock("@/lib/api").api as {
  get: jest.Mock;
  post: jest.Mock;
  delete: jest.Mock;
};

import {
  UploadResultProvider,
  useUploadResult,
  type UploadResult,
} from "../app/dashboard/upload-result-context";
import { AuthLayout, AuthSubmitButton } from "../src/components/AuthLayout";
import { LoadingSpinner } from "../src/components/LoadingSpinner";
import { useChat } from "../src/hooks/useChat";
import { useDashboard } from "../src/hooks/useDashboard";
import { useJobs } from "../src/hooks/useJobs";
import { useMobileNav } from "../src/hooks/useMobileNav";
import { useRoles } from "../src/hooks/useRoles";
import { useSettings } from "../src/hooks/useSettings";
import { useSkills } from "../src/hooks/useSkills";
import { useUpload } from "../src/hooks/useUpload";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

function wrapper({ children }: { children: React.ReactNode }) {
  return <UploadResultProvider>{children}</UploadResultProvider>;
}

describe("frontend hooks, components, and upload context", () => {
  beforeEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
    mockPathname = "/dashboard";
    Object.defineProperty(window.navigator, "webdriver", {
      configurable: true,
      value: false,
    });
    document.body.style.overflow = "";
  });

  it("renders shared auth and loading components", () => {
    render(
      <AuthLayout
        title="Welcome"
        subtitle="Sign in"
        serverError="Nope"
        footerPrompt="Need account?"
        footerHref="/register"
        footerLinkText="Register"
        blobVariant="register"
      >
        <input aria-label="Email" />
      </AuthLayout>,
    );

    expect(screen.getByText("Welcome")).toBeInTheDocument();
    expect(screen.getByText("Nope")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Register" })).toHaveAttribute("href", "/register");

    render(<AuthSubmitButton loading loadingText="Working" idleText="Submit" />);
    expect(screen.getByRole("button", { name: /working/i })).toBeDisabled();

    render(<LoadingSpinner label="Loading data" />);
    expect(screen.getByText("Loading data")).toBeInTheDocument();
  });

  it("stores, clears, and guards upload result context", () => {
    const sample: UploadResult = {
      all_skills: ["python"],
      rule_based_skills: ["python"],
      llm_skills: [],
      recommended_roles: [],
    };

    function Consumer() {
      const { uploadResult, setUploadResult, clearUploadResult } = useUploadResult();
      return (
        <>
          <div data-testid="value">{uploadResult?.all_skills.join(",") ?? "empty"}</div>
          <button onClick={() => setUploadResult(sample)}>set</button>
          <button onClick={clearUploadResult}>clear</button>
        </>
      );
    }

    render(
      <UploadResultProvider>
        <Consumer />
      </UploadResultProvider>,
    );
    expect(screen.getByTestId("value")).toHaveTextContent("empty");
    fireEvent.click(screen.getByText("set"));
    expect(screen.getByTestId("value")).toHaveTextContent("python");
    fireEvent.click(screen.getByText("clear"));
    expect(screen.getByTestId("value")).toHaveTextContent("empty");

    expect(screen.queryByText("python")).not.toBeInTheDocument();
  });

  it("sends chat messages and appends success or fallback responses", async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: "Hello back" } });
    const { result } = renderHook(() => useChat());

    act(() => result.current.setInput("  hi  "));
    await act(async () => {
      await result.current.send({ preventDefault: jest.fn() } as unknown as React.FormEvent);
    });

    expect(mockApi.post).toHaveBeenCalledWith("/chatbot/", {
      messages: [{ role: "user", content: "hi" }],
    });
    expect(result.current.messages).toEqual([
      { role: "user", content: "hi" },
      { role: "assistant", content: "Hello back" },
    ]);

    mockApi.post.mockRejectedValueOnce(new Error("network"));
    act(() => result.current.setInput("again"));
    await act(async () => {
      await result.current.send({ preventDefault: jest.fn() } as unknown as React.FormEvent);
    });
    expect(result.current.messages.at(-1)).toEqual({
      role: "assistant",
      content: "Sorry, I could not respond.",
    });
  });

  it("ignores blank chat sends and locked loading sends", async () => {
    const hold = deferred<{ data: { message: string } }>();
    mockApi.post.mockReturnValueOnce(hold.promise);
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.send({ preventDefault: jest.fn() } as unknown as React.FormEvent);
    });
    expect(mockApi.post).not.toHaveBeenCalled();

    act(() => result.current.setInput("slow"));
    let firstSend!: Promise<void>;
    await act(async () => {
      firstSend = result.current.send({ preventDefault: jest.fn() } as unknown as React.FormEvent);
      await Promise.resolve();
    });
    await waitFor(() => expect(result.current.loading).toBe(true));
    await act(async () => {
      await result.current.send({ preventDefault: jest.fn() } as unknown as React.FormEvent);
    });
    expect(mockApi.post).toHaveBeenCalledTimes(1);
    await act(async () => {
      hold.resolve({ data: { message: "done" } });
      await firstSend;
    });
  });

  it("loads dashboard data and uses Playwright fallback data", async () => {
    mockApi.get.mockResolvedValueOnce({ data: { match_score: 1, top_roles: [], skill_distribution: [], skill_gaps: {}, learning_plan: [], job_matches: [] } });
    const { result, unmount } = renderHook(() => useDashboard());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data?.match_score).toBe(1);
    unmount();

    Object.defineProperty(window.navigator, "webdriver", {
      configurable: true,
      value: true,
    });
    const fallback = renderHook(() => useDashboard());
    await waitFor(() => expect(fallback.result.current.loading).toBe(false));
    expect(fallback.result.current.data?.top_roles[0].title).toBe("Frontend Developer");
  });

  it("loads jobs, supports search/page refresh, and switches display tabs", async () => {
    jest.useFakeTimers();
    mockApi.get
      .mockResolvedValueOnce({ data: { results: [{ id: "m1", title: "Matched" }] } })
      .mockResolvedValueOnce({ data: { results: [{ id: "a1", title: "All" }], total: 30 } })
      .mockResolvedValueOnce({ data: { total_jobs: 30, matched_count: 1, last_synced: null } })
      .mockResolvedValue({ data: { results: [], total: 0 } });

    const { result } = renderHook(() => useJobs());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.displayJobs[0].id).toBe("m1");
    expect(result.current.totalPages).toBe(2);

    act(() => result.current.setTab("all"));
    expect(result.current.displayJobs[0].id).toBe("a1");

    await act(async () => {
      await result.current.handleRefresh();
    });
    expect(result.current.refreshing).toBe(false);

    act(() => result.current.setSearch("react"));
    await act(async () => {
      jest.advanceTimersByTime(350);
      await Promise.resolve();
    });
    expect(mockApi.get).toHaveBeenCalledWith("/jobs/matched/?q=react");

    act(() => result.current.setPage(2));
    await act(async () => {
      await Promise.resolve();
    });
    expect(mockApi.get).toHaveBeenCalledWith("/jobs/?page=2&per_page=15&q=react");
  });

  it("opens and closes mobile nav while locking body scroll", () => {
    const hook = renderHook(() => useMobileNav());
    act(() => hook.result.current.openMenu());
    expect(hook.result.current.mobileOpen).toBe(true);
    expect(document.body.style.overflow).toBe("hidden");
    act(() => hook.result.current.closeMenu());
    expect(document.body.style.overflow).toBe("");

    mockPathname = "/dashboard/jobs";
    hook.rerender();
    expect(hook.result.current.mobileOpen).toBe(false);
  });

  it("loads roles and computes resume role scores from context or database fallback", async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: { roles: [{ id: "r1", title: "Engineer" }] } })
      .mockResolvedValueOnce({ data: { recommended_roles: [{ role: "DB", description: "", skills: "SQL", score: 0 }] } })
      .mockResolvedValueOnce({ data: [{ id: "s1", skill_name: "Python" }] });

    const { result } = renderHook(() =>
      useRoles([{ role: "Context", description: "", skills: "Python, React", score: 0 }]),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.roles[0].title).toBe("Engineer");
    expect(result.current.fromResume[0].score).toBe(0.5);

    mockApi.get.mockRejectedValue({ data: {} });
    const fallback = renderHook(() => useRoles([]));
    await waitFor(() => expect(fallback.result.current.loading).toBe(false));
    expect(fallback.result.current.fromResume).toEqual([]);
  });

  it("loads settings and redirects after logout even when logout request fails", async () => {
    mockApi.get.mockResolvedValueOnce({ data: { id: "u1", email: "me@example.com", is_active: true, created_at: "now" } });
    mockApi.post.mockRejectedValueOnce(new Error("logout failed"));
    const { result } = renderHook(() => useSettings());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user?.email).toBe("me@example.com");
    await act(async () => {
      await result.current.handleLogout();
    });
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  it("loads, adds, removes, and validates skills", async () => {
    mockApi.get.mockResolvedValue({ data: [{ id: "s1", skill_name: "Python", source: "manual" }] });
    mockApi.post.mockResolvedValue({});
    mockApi.delete.mockResolvedValue({});
    const { result } = renderHook(() => useSkills());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.skills).toHaveLength(1);

    await act(async () => {
      await result.current.addSkill("  ");
    });
    expect(mockApi.post).not.toHaveBeenCalled();

    await act(async () => {
      await result.current.addSkill(" React ");
    });
    expect(mockApi.post).toHaveBeenCalledWith("/skills/manual/", { name: "React" });

    await act(async () => {
      await result.current.removeSkill("s1");
    });
    expect(mockApi.delete).toHaveBeenCalledWith("/skills/s1/");
  });

  it("validates and uploads resumes through upload hook", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: {
        all_skills: ["python"],
        rule_based_skills: ["python"],
        llm_skills: [],
        recommended_roles: [],
      },
    });
    const { result } = renderHook(() => useUpload(), { wrapper });

    await act(async () => {
      await result.current.handleUpload();
    });
    expect(result.current.message).toBe("Please select a PDF file.");

    act(() => {
      result.current.handleFileChange({
        target: { files: [new File(["x"], "resume.txt", { type: "text/plain" })] },
      } as unknown as React.ChangeEvent<HTMLInputElement>);
    });
    expect(result.current.message).toBe("Please select a PDF file only.");

    act(() => {
      result.current.handleFileChange({
        target: { files: [new File(["pdf"], "resume.pdf", { type: "application/pdf" })] },
      } as unknown as React.ChangeEvent<HTMLInputElement>);
    });
    await act(async () => {
      await result.current.handleUpload();
    });
    expect(result.current.success).toBe(true);
    expect(result.current.message).toBe("Upload successful! Skills and roles have been extracted.");

    mockApi.post.mockRejectedValueOnce({ response: { data: { error: "Bad PDF" } } });
    await act(async () => {
      await result.current.handleUpload();
    });
    expect(result.current.success).toBe(false);
    expect(result.current.message).toBe("Bad PDF");
  });
});
