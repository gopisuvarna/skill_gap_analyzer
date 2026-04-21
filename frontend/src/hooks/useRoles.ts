import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export interface Role {
  id: string;
  title: string;
  description: string;
  required_skills?: string[];
  match_score?: number;        // now computed server-side and returned directly
}

export interface ResumeRole {
  role: string;
  description: string;
  skills: string;              // comma-separated skill names from AI extraction
  score: number;               // recomputed client-side against live user skills
}
function parseSkillSet(skills: string): Set<string> {
  return new Set(
    skills
      .split(",")
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
}
function computeScore(
  required: Set<string> | string[],
  userSkillNames: Set<string>,
): number | null {
  const req = Array.isArray(required) ? required : [...required];
  if (req.length === 0) return null;
  const matched = req.filter((s) => userSkillNames.has(s.toLowerCase())).length;
  return matched / req.length;
}

export function useRoles(contextRoles: ResumeRole[]) {
  const [roles, setRoles]                   = useState<Role[]>([]);
  const [dbResumeRoles, setDbResumeRoles]   = useState<ResumeRole[]>([]);
  const [userSkillNames, setUserSkillNames] = useState<Set<string>>(new Set());
  const [loading, setLoading]               = useState<boolean>(true);

  useEffect(() => {
    Promise.all([
      api
        .get<{ roles: Role[] }>("/recommendations/roles/")
        .then((r) => setRoles(r.data.roles ?? []))
        .catch(() => {}),
      api
        .get<{ recommended_roles: ResumeRole[] }>("/documents/latest-roles/")
        .then((r) => setDbResumeRoles(r.data.recommended_roles ?? []))
        .catch(() => {}),
      api
        .get<{ id: string; skill_name: string }[]>("/skills/")
        .then((r) => {
          setUserSkillNames(
            new Set((r.data ?? []).map((us) => us.skill_name.toLowerCase())),
          );
        })
        .catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);
  const rawResumeRoles = contextRoles.length > 0 ? contextRoles : dbResumeRoles;
  const fromResume: ResumeRole[] = rawResumeRoles.map((r) => ({
    ...r,
    score: computeScore(parseSkillSet(r.skills), userSkillNames) ?? 0,
  }));
  return { roles, fromResume, loading };
}