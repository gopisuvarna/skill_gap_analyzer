import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export interface UserSkill {
  id: string;
  skill_name: string;
  source: string;
}

export function useSkills() {
  const [skills, setSkills] = useState<UserSkill[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [adding, setAdding] = useState<boolean>(false); // FIX: loading state for add
  const [removingId, setRemovingId] = useState<string | null>(null); // FIX: loading state for remove

  useEffect(() => {
    loadSkills();
    const fallback = setTimeout(() => setLoading(false), 5000);
    return () => clearTimeout(fallback);
  }, []);

  function loadSkills() {
    api
      .get<UserSkill[]>("/skills/")
      .then((r) => setSkills(r.data))
      .catch(() => setSkills([]))
      .finally(() => setLoading(false));
  }

  async function addSkill(name: string) {
    if (!name.trim()) return;
    setAdding(true);
    try {
      await api.post("/skills/manual/", { name: name.trim() });
      loadSkills();
    } finally {
      setAdding(false);
    }
  }

  async function removeSkill(id: string) {
    setRemovingId(id);
    try {
      await api.delete(`/skills/${id}/`);
      loadSkills();
    } finally {
      setRemovingId(null);
    }
  }

  return { skills, loading, adding, removingId, addSkill, removeSkill };
}
