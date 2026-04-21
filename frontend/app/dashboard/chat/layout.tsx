import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Career Mentor — AI Skill Sync",
};

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
