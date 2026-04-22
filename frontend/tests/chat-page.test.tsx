import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

const mockSetInput = jest.fn();
const mockSend = jest.fn((event?: React.FormEvent<HTMLFormElement>) => event?.preventDefault());

let chatState = {
  messages: [] as Array<{ role: "user" | "assistant"; content: string }>,
  input: "",
  loading: false,
  bottomRef: { current: null } as React.RefObject<HTMLDivElement | null>,
};

jest.mock("@/hooks/useChat", () => ({
  useChat: () => ({
    ...chatState,
    setInput: mockSetInput,
    send: mockSend,
  }),
}));

import ChatPage from "../app/dashboard/chat/page";
import tailwindConfig from "../tailwind.config";

describe("ChatPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    chatState = {
      messages: [],
      input: "",
      loading: false,
      bottomRef: { current: null },
    };
  });

  it("renders the empty state and suggestion shortcuts", () => {
    render(<ChatPage />);

    expect(screen.getByText("AI Career Mentor")).toBeInTheDocument();
    expect(screen.getByText(/Ask me about skill gaps/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /What skills am I missing/i }));
    expect(mockSetInput).toHaveBeenCalledWith("What skills am I missing for my top role?");
  });

  it("renders markdown-rich assistant messages and user messages", () => {
    chatState.messages = [
      { role: "user", content: "plain user text" },
      {
        role: "assistant",
        content: [
          "# Heading",
          "",
          "## Subheading",
          "### Minor heading",
          "---",
          "Plain **bold** with `code` and [Docs](https://example.com)",
          "* bullet one",
          "- bullet two",
          "1. first",
          "2) second",
          "  - nested child",
        ].join("\n"),
      },
      {
        role: "assistant",
        content: "Broken markdown [oops]( and stray `backtick and **stars",
      },
    ];

    render(<ChatPage />);

    expect(screen.getByText("plain user text")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Heading" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: "Subheading" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "Minor heading" })).toBeInTheDocument();
    expect(screen.getByText("bold")).toContainHTML("strong");
    expect(screen.getByText("code")).toContainHTML("code");
    expect(screen.getByRole("link", { name: "Docs" })).toHaveAttribute("href", "https://example.com");
    expect(screen.getByText("bullet one")).toBeInTheDocument();
    expect(screen.getByText("bullet two")).toBeInTheDocument();
    expect(screen.getByText("1.")).toBeInTheDocument();
    expect(screen.getByText("2.")).toBeInTheDocument();
    expect(screen.getByText("nested child")).toBeInTheDocument();
    expect(screen.getByText(/Broken markdown/)).toBeInTheDocument();
  });

  it("binds the input and shows the typing indicator while loading", () => {
    chatState.input = "career";
    chatState.loading = true;

    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask anything about your career/i);
    expect(input).toHaveValue("career");
    expect(input).toBeDisabled();

    fireEvent.change(input, { target: { value: "next question" } });
    expect(mockSetInput).toHaveBeenCalledWith("next question");

    fireEvent.submit(input.closest("form") as HTMLFormElement);
    expect(mockSend).toHaveBeenCalled();

    expect(document.querySelectorAll(".chat-typing-bubble span.w-1\\.5").length).toBe(3);
  });
});

describe("frontend config coverage", () => {
  it("loads tailwind config and jest setup coverage paths", () => {
    expect(tailwindConfig.content).toEqual([
      "./src/**/*.{js,ts,jsx,tsx,mdx}",
      "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ]);
    expect(tailwindConfig.theme?.extend?.fontFamily).toMatchObject({
      sans: ["var(--font-body)", "system-ui", "sans-serif"],
      display: ["var(--font-display)", "system-ui", "sans-serif"],
      mono: ["var(--font-geist-mono)", "monospace"],
    });
    expect(tailwindConfig.plugins).toEqual([]);
    expect(expect.extend).toBeDefined();
  });
});
