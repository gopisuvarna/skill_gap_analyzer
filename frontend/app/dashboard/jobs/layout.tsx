import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Jobs — AI Skill Sync",
};

export default function JobsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
