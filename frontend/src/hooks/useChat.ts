import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const msgs = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const res = await api.post<{ message: string }>("/chatbot/", {
        messages: msgs,
      });
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.data.message },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry, I could not respond." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return { messages, input, setInput, loading, send, bottomRef };
}
