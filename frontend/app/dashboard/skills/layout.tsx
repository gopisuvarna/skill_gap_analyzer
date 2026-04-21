import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Skills — AI Skill Sync",
};

export default function SkillsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
