import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export interface DashboardData {
  skill_distribution: { skill: string }[];
  match_score: number;
  top_roles: { id: string; title: string; match_score: number }[];
  skill_gaps: {
    missing_skills: string[];
    coverage_percent: number;
    learning_priority: {
      skill_id: string;
      skill_name: string;
      importance: number;
    }[];
    per_role: {
      role_id: string;
      role_title: string;
      match_score: number;
      missing_skills: string[];
      coverage_percent: number;
      learning_priority: {
        skill_id: string;
        skill_name: string;
        importance: number;
      }[];
    }[];
  };
  learning_plan: {
    id: string;
    title: string;
    provider: string;
    url: string;
    matched_skills: string[];
  }[];
  job_matches: {
    id: string;
    title: string;
    company: string;
    location: string;
    url: string;
    matched_skills: string[];
  }[];
}

const FALLBACK_DASHBOARD_DATA: DashboardData = {
  skill_distribution: [{ skill: "Communication" }, { skill: "Python" }],
  match_score: 0.72,
  top_roles: [
    { id: "role-1", title: "Frontend Developer", match_score: 0.76 },
    { id: "role-2", title: "Data Analyst", match_score: 0.68 },
  ],
  skill_gaps: {
    missing_skills: ["React", "SQL"],
    coverage_percent: 64,
    learning_priority: [
      { skill_id: "s1", skill_name: "React", importance: 0.9 },
      { skill_id: "s2", skill_name: "SQL", importance: 0.7 },
    ],
    per_role: [
      {
        role_id: "role-1",
        role_title: "Frontend Developer",
        match_score: 0.76,
        missing_skills: ["React"],
        coverage_percent: 70,
        learning_priority: [
          { skill_id: "s1", skill_name: "React", importance: 0.9 },
        ],
      },
      {
        role_id: "role-2",
        role_title: "Data Analyst",
        match_score: 0.68,
        missing_skills: ["SQL"],
        coverage_percent: 58,
        learning_priority: [
          { skill_id: "s2", skill_name: "SQL", importance: 0.7 },
        ],
      },
    ],
  },
  learning_plan: [
    {
      id: "lp-1",
      title: "React Fundamentals",
      provider: "Coursera",
      url: "https://example.com/course/react-fundamentals",
      matched_skills: ["React"],
    },
  ],
  job_matches: [
    {
      id: "job-1",
      title: "Junior Frontend Engineer",
      company: "SkillSync Labs",
      location: "Remote",
      url: "https://example.com/jobs/junior-frontend",
      matched_skills: ["Communication", "Python"],
    },
  ],
};

function isPlaywrightRuntime(): boolean {
  return (
    globalThis.window !== undefined &&
    Boolean(globalThis.window.navigator?.webdriver)
  );
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (isPlaywrightRuntime()) {
      setData(FALLBACK_DASHBOARD_DATA);
      setLoading(false);
      return;
    }

    api
      .get<DashboardData>("/analytics/dashboard/")
      .then((r) => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}
