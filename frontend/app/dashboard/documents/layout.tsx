import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Resume Upload — AI Skill Sync",
};

export default function DocumentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
