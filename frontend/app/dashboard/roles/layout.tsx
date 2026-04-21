import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Roles — AI Skill Sync",
};

export default function RolesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
