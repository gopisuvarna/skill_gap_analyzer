"use client";

import { useChat } from "@/hooks/useChat";
import React from "react";

type InlineToken =
  | { type: "text"; value: string }
  | { type: "bold"; value: string }
  | { type: "code"; value: string }
  | { type: "link"; value: string };

type TokenReadResult = { token: InlineToken; nextIndex: number } | null;

function readBoldToken(text: string, index: number): TokenReadResult {
  if (!text.startsWith("**", index)) return null;
  const end = text.indexOf("**", index + 2);
  if (end <= index + 2) return null;
  return {
    token: { type: "bold", value: text.slice(index + 2, end) },
    nextIndex: end + 2,
  };
}

function readCodeToken(text: string, index: number): TokenReadResult {
  if (text[index] !== "`") return null;
  const end = text.indexOf("`", index + 1);
  if (end <= index + 1) return null;
  return {
    token: { type: "code", value: text.slice(index + 1, end) },
    nextIndex: end + 1,
  };
}

function readLinkToken(text: string, index: number): TokenReadResult {
  if (text[index] !== "[") return null;
  const closeLabel = text.indexOf("]", index + 1);
  if (closeLabel === -1 || text[closeLabel + 1] !== "(") return null;
  const closeUrl = text.indexOf(")", closeLabel + 2);
  if (closeUrl <= closeLabel + 2) return null;
  return {
    token: { type: "link", value: text.slice(index, closeUrl + 1) },
    nextIndex: closeUrl + 1,
  };
}

function findNextSpecialIndex(text: string, index: number): number {
  let next = index + 1;
  while (next < text.length) {
    if (
      text.startsWith("**", next) ||
      text[next] === "`" ||
      text[next] === "["
    ) {
      return next;
    }
    next++;
  }
  return next;
}

function readSpecialToken(text: string, index: number): TokenReadResult {
  return (
    readBoldToken(text, index) ??
    readCodeToken(text, index) ??
    readLinkToken(text, index)
  );
}

function splitInlineTokens(text: string): InlineToken[] {
  const tokens: InlineToken[] = [];
  let i = 0;

  while (i < text.length) {
    const special = readSpecialToken(text, i);
    if (special) {
      tokens.push(special.token);
      i = special.nextIndex;
      continue;
    }

    const next = findNextSpecialIndex(text, i);
    tokens.push({ type: "text", value: text.slice(i, next) });
    i = next;
  }

  return tokens.filter((token) => token.value.length > 0);
}

function parseMarkdownLink(
  token: string,
): { label: string; href: string } | null {
  if (!token.startsWith("[") || !token.endsWith(")")) return null;

  const closeLabel = token.indexOf("]");
  if (closeLabel <= 1) return null;
  if (token[closeLabel + 1] !== "(") return null;

  const label = token.slice(1, closeLabel);
  const href = token.slice(closeLabel + 2, -1);
  if (!href) return null;

  return { label, href };
}

function renderInline(text: string): React.ReactNode {
  return splitInlineTokens(text).map((token, idx) => {
    // S6479: stable key = position + first chars of content
    const key = `${idx}-${token.value.slice(0, 12)}`;

    if (token.type === "bold")
      return (
        <strong key={key} className="color-primary" style={{ fontWeight: 600 }}>
          {token.value}
        </strong>
      );

    if (token.type === "code")
      return (
        <code key={key} className="md-code">
          {token.value}
        </code>
      );

    if (token.type === "link") {
      const link = parseMarkdownLink(token.value);
      if (!link)
        return <React.Fragment key={key}>{token.value}</React.Fragment>;
      return (
        <a
          key={key}
          href={link.href}
          target="_blank"
          rel="noopener noreferrer"
          className="md-link"
        >
          {link.label}
        </a>
      );
    }

    return <React.Fragment key={key}>{token.value}</React.Fragment>;
  });
}

/* ── MarkdownMessage helpers (S3776: reduce cognitive complexity) ── */

const HR_RE = /^[=-]{3,}$/; // S6535: \- → - (no escape needed in class)
const OL_RE = /^\d+[.)]\s/;
const NESTED_LI_RE = /^\s{2,}[*-]\s/; // S6535: \- → -

function renderHeading(
  trimmed: string,
  level: number,
  key: number,
): React.ReactNode {
  const slice = trimmed.slice(level + 1);
  if (level === 1)
    return (
      <h2 key={key} className="md-h1">
        {renderInline(slice)}
      </h2>
    );
  if (level === 2)
    return (
      <h3 key={key} className="md-h2">
        {renderInline(slice)}
      </h3>
    );
  return (
    <h4 key={key} className="md-h3">
      {renderInline(slice)}
    </h4>
  );
}

function renderUnorderedList(
  items: string[],
  baseKey: number,
): React.ReactNode {
  return (
    <ul
      key={`ul-${baseKey}`}
      style={{ margin: "0.2rem 0", padding: 0, listStyle: "none" }}
    >
      {items.map((item) => (
        // S6479: stable key = item content
        <li key={item} className="flex gap-1.5 mb-0.5 items-start">
          <span className="md-bullet">•</span>
          <span className="md-li-text">{renderInline(item)}</span>
        </li>
      ))}
    </ul>
  );
}

function renderOrderedList(items: string[], baseKey: number): React.ReactNode {
  return (
    <ol
      key={`ol-${baseKey}`}
      style={{ margin: "0.2rem 0", padding: 0, listStyle: "none" }}
    >
      {items.map((item, idx) => (
        // S6479: stable key = position + content
        <li
          key={`${idx}-${item.slice(0, 12)}`}
          className="flex gap-2 mb-0.5 items-start"
        >
          <span className="md-num">{idx + 1}.</span>
          <span className="md-li-text">{renderInline(item)}</span>
        </li>
      ))}
    </ol>
  );
}

function collectBulletItems(
  lines: string[],
  start: number,
): { items: string[]; end: number } {
  const items: string[] = [];
  let i = start;
  while (i < lines.length) {
    const t = lines[i].trim();
    if (t.startsWith("* ") || t.startsWith("- ")) {
      items.push(t.slice(2));
      i++;
    } else {
      break;
    }
  }
  return { items, end: i };
}

function collectOrderedItems(
  lines: string[],
  start: number,
): { items: string[]; end: number } {
  const items: string[] = [];
  let i = start;
  while (i < lines.length && OL_RE.exec(lines[i].trim())) {
    items.push(lines[i].trim().replace(OL_RE, ""));
    i++;
  }
  return { items, end: i };
}

// S3776 + S6759: extracted parsing logic; props marked readonly
function parseLine(
  lines: string[],
  i: number,
  elements: React.ReactNode[],
): number {
  const line = lines[i];
  const trimmed = line.trim();

  if (!trimmed) {
    elements.push(<div key={`sp-${i}`} style={{ height: "0.35rem" }} />);
    return i + 1;
  }

  if (trimmed.startsWith("### ")) {
    elements.push(renderHeading(trimmed, 3, i));
    return i + 1;
  }
  if (trimmed.startsWith("## ")) {
    elements.push(renderHeading(trimmed, 2, i));
    return i + 1;
  }
  if (trimmed.startsWith("# ")) {
    elements.push(renderHeading(trimmed, 1, i));
    return i + 1;
  }

  // S6594: use RegExp.exec()
  if (HR_RE.exec(trimmed)) {
    elements.push(<hr key={i} className="md-hr" />);
    return i + 1;
  }

  if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
    const { items, end } = collectBulletItems(lines, i);
    elements.push(renderUnorderedList(items, i));
    return end;
  }

  // S6594: use RegExp.exec()
  if (OL_RE.exec(trimmed)) {
    const { items, end } = collectOrderedItems(lines, i);
    elements.push(renderOrderedList(items, i));
    return end;
  }

  // S6594: use RegExp.exec()
  if (NESTED_LI_RE.exec(line)) {
    elements.push(
      <li
        key={i}
        className="flex gap-1.5 ml-6 mb-0.5 items-start"
        style={{ listStyle: "none" }}
      >
        <span className="md-sub-arrow">→</span>
        <span className="md-sub-text">{renderInline(trimmed.slice(2))}</span>
      </li>,
    );
    return i + 1;
  }

  elements.push(
    <p key={i} className="md-p">
      {renderInline(trimmed)}
    </p>,
  );
  return i + 1;
}

// S6759: mark props as read-only
interface MarkdownMessageProps {
  readonly content: string;
}

function MarkdownMessage({ content }: MarkdownMessageProps) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    i = parseLine(lines, i, elements);
  }
  return <div style={{ fontSize: "0.875rem" }}>{elements}</div>;
}

/* ── Page ─────────────────────────────────────────────────── */
const SUGGESTIONS = [
  "What skills am I missing for my top role?",
  "Give me a learning roadmap for Docker",
  "How ready am I for a Data Scientist role?",
  "What should I learn next?",
];

const TYPING_DOTS = ["dot-a", "dot-b", "dot-c"] as const;

export default function ChatPage() {
  const { messages, input, setInput, loading, send, bottomRef } = useChat();

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 mb-4 chat-header-border">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center text-sm chat-header-icon">
          ✦
        </div>
        <div>
          <h1 className="text-lg chat-header-title">AI Career Mentor</h1>
          <p className="text-xs chat-header-sub">
            Ask about skills, paths, or job readiness
          </p>
        </div>
        {/* S6772: explicit space between sibling spans avoided by using flex gap */}
        <div className="ml-auto flex items-center gap-1.5 text-xs chat-online">
          <span className="w-1.5 h-1.5 rounded-full chat-online-dot" />
          <span>Online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 pb-8">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl chat-empty-icon">
              🤖
            </div>
            <p
              className="text-center text-sm chat-empty-text"
              style={{ maxWidth: "22rem" }}
            >
              Hi! I&apos;m your AI Career Mentor. Ask me about skill gaps,
              career transitions, job readiness, or anything career-related.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-sm mt-2">
              {/* S6479: suggestion text is unique — use it directly as key */}
              {SUGGESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="chat-suggestion text-xs text-left px-3 py-2.5 rounded-lg transition-all"
                >
                  &ldquo;{q}&rdquo;
                </button>
              ))}
            </div>
          </div>
        ) : (
          // S6479: use role + first 20 chars of content as stable key
          messages.map((m, i) => (
            <div
              key={`${m.role}-${m.content.slice(0, 20)}-${i}`}
              className={`flex gap-3 anim-fade-up ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div
                className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                  m.role === "user" ? "chat-avatar-user" : "chat-avatar-ai"
                }`}
              >
                {m.role === "user" ? "U" : "✦"}
              </div>
              <div
                className={
                  m.role === "user"
                    ? "max-w-[78%] sm:max-w-[70%]"
                    : "max-w-[90%] sm:max-w-[85%]"
                }
              >
                <div
                  className={`rounded-2xl ${m.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}`}
                >
                  {m.role === "user" ? (
                    m.content
                  ) : (
                    <MarkdownMessage content={m.content} />
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="flex gap-3 anim-fade-in">
            <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs chat-avatar-ai">
              ✦
            </div>
            <div className="rounded-2xl px-4 py-3 chat-typing-bubble">
              <span className="flex gap-1 items-center">
                {/* S6479: use named string IDs, not array index */}
                {TYPING_DOTS.map((id, j) => (
                  <span
                    key={id}
                    className="w-1.5 h-1.5 rounded-full inline-block"
                    style={{
                      background: "var(--text-muted)",
                      animation: `bounce 1s ${j * 0.2}s infinite`,
                    }}
                  />
                ))}
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={send} className="flex gap-2 mt-4 pt-4 chat-header-border">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything about your career…"
          disabled={loading}
          className="input flex-1"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="btn btn-primary px-5"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>

      <style>{`
        @keyframes bounce {
          0%, 100% { opacity: 0.3; transform: translateY(0); }
          50%       { opacity: 1;   transform: translateY(-3px); }
        }
      `}</style>
    </div>
  );
}
