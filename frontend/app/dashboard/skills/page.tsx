"use client";

import { useState } from "react";
import { useSkills } from "@/hooks/useSkills";
import { useUploadResult } from "../upload-result-context";
import { LoadingSpinner } from "@/components/LoadingSpinner";

// Animation delay step constant
const ANIM_STEP = 0.03;

export default function SkillsPage() {
  const { skills, loading, adding, removingId, addSkill, removeSkill } =
    useSkills();
  const { uploadResult } = useUploadResult();
  const [newSkill, setNewSkill] = useState("");

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!newSkill.trim()) return;
    try {
      await addSkill(newSkill);
      setNewSkill("");
    } catch {
      /* ignore */
    }
  }

  async function handleRemove(id: string) {
    try {
      await removeSkill(id);
    } catch {
      /* ignore */
    }
  }

  if (loading) return <LoadingSpinner label="Loading skills…" />;

  const contextSkills = uploadResult?.all_skills ?? [];
  const dbResumeSkills = skills
    .filter((s) => s.source === "document")
    .map((s) => s.skill_name);
  const extractedSkills =
    contextSkills.length > 0 ? contextSkills : dbResumeSkills;

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="font-display" style={{ marginBottom: "0.35rem" }}>
          Skills
        </h1>
        <p className="text-sm color-muted">
          Manage your skill profile to get better job and role matches.
        </p>
      </div>

      {/* Resume-extracted skills */}
      {extractedSkills.length > 0 && (
        <div className="card card-md anim-fade-up">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-base">📄</span>
            <h2 className="text-base" style={{ margin: 0 }}>
              Extracted from Resume
            </h2>
            <span className="ml-auto badge badge-accent">
              {extractedSkills.length} skills
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {extractedSkills.map((skill, i) => (
              <span
                key={skill}
                className="badge badge-brand anim-fade-up"
                style={{ animationDelay: `${i * ANIM_STEP}s` }}
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Manually added skills */}
      <div className="card card-md anim-fade-up delay-1">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-base">🛠</span>
          <h2 className="text-base" style={{ margin: 0 }}>
            Your Skills
          </h2>
          <span className="ml-auto badge badge-brand">{skills.length}</span>
        </div>

        {/* Add skill form — FIX: button shows loading state while adding */}
        <form onSubmit={handleAdd} className="flex gap-2 mb-5">
          <input
            type="text"
            placeholder="e.g. Python, Project Management…"
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            disabled={adding}
            className="input flex-1"
          />
          <button
            type="submit"
            disabled={adding || !newSkill.trim()}
            className="btn btn-primary px-5"
          >
            {adding ? (
              <span className="flex items-center gap-1.5">
                <svg
                  className="animate-spin w-3.5 h-3.5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Adding…
              </span>
            ) : (
              "Add"
            )}
          </button>
        </form>

        {skills.length === 0 ? (
          <p className="text-sm text-center py-4 color-muted">
            No skills added yet. Add your first skill above.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {skills.map((s, i) => (
              <span
                key={s.id}
                className="skill-tag inline-flex items-center gap-1.5 anim-fade-up"
                style={{ animationDelay: `${i * ANIM_STEP}s` }}
              >
                {/* FIX: show spinner on the skill being removed */}
                {removingId === s.id ? (
                  <svg
                    className="animate-spin w-3 h-3 color-muted"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                ) : null}
                {s.skill_name}
                {/* FIX: removed onMouseOver/onMouseOut — handled by CSS .skill-remove-btn:hover */}
                <button
                  onClick={() => handleRemove(s.id)}
                  disabled={removingId === s.id}
                  aria-label={`Remove ${s.skill_name}`}
                  className="skill-remove-btn flex items-center justify-center w-4 h-4 rounded-full text-xs"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
