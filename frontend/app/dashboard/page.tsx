"use client";

import Link from "next/link";
import { useState } from "react";
import { useDashboard } from "@/hooks/useDashboard";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import "@/styles/components.css";

type StatCardProps = Readonly<{
  label: string;
  value: string;
  sub?: string;
  color?: string;
}>;

type ProgressRingProps = Readonly<{ score: number }>;

interface PrioritySkill {
  skill_name: string;
  importance: number;
}

type SkillBadgeProps = Readonly<{ name: string; importance: number }>;

type SkillGapGroupProps = Readonly<{
  skills: PrioritySkill[];
  expanded: boolean;
  onToggle: () => void;
  visibleCount: number;
}>;

function getCoverageColor(pct: number): string {
  if (pct >= 80) return "var(--success)";
  if (pct >= 50) return "var(--brand-500)";
  return "var(--warning)";
}

function getScoreColor(pct: number): string {
  if (pct >= 75) return "var(--success)";
  if (pct >= 50) return "var(--brand-500)";
  return "var(--warning)";
}

function pluralSuffix(count: number): string {
  return count === 1 ? "" : "s";
}

/* ── Stat card ────────────────────────────────────────────── */
function StatCard({ label, value, sub, color }: StatCardProps) {
  return (
    <div className="card card-sm anim-fade-up">
      <p className="stat-label">{label}</p>
      <p className="stat-value" style={{ color: color ?? "var(--brand-500)" }}>
        {value}
      </p>
      {sub && <p className="stat-sub">{sub}</p>}
    </div>
  );
}

/* ── Progress ring ────────────────────────────────────────── */
function ProgressRing({ score }: ProgressRingProps) {
  const pct = Math.round(score * 100);
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  const color = getScoreColor(pct);

  return (
    <div className="card progress-ring-card anim-fade-up delay-1 flex flex-col items-center justify-center">
      <p className="stat-label">Match Score</p>
      <div className="relative w-24 h-24 flex items-center justify-center">
        <svg
          width="96"
          height="96"
          viewBox="0 0 96 96"
          style={{ transform: "rotate(-90deg)" }}
        >
          <circle
            cx="48"
            cy="48"
            r={r}
            fill="none"
            stroke="var(--border-subtle)"
            strokeWidth="7"
          />
          <circle
            cx="48"
            cy="48"
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="7"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.8s ease" }}
          />
        </svg>
        <span
          className="absolute text-xl font-bold"
          style={{ fontFamily: "var(--font-display)", color }}
        >
          {pct}%
        </span>
      </div>
      <p className="stat-sub">Overall readiness</p>
    </div>
  );
}

/* ── Skill badge ──────────────────────────────────────────── */
function SkillBadge({ name, importance }: SkillBadgeProps) {
  const isHigh = importance >= 0.8;
  const isMed = importance >= 0.5;
  let variant = "skill-badge-low";
  let dot = "skill-dot-low";
  let label = "Low";

  if (isHigh) {
    variant = "skill-badge-high";
    dot = "skill-dot-high";
    label = "High";
  } else if (isMed) {
    variant = "skill-badge-med";
    dot = "skill-dot-med";
    label = "Med";
  }

  return (
    <span
      className={`badge flex items-center gap-1.5 ${variant}`}
      style={{ fontSize: "0.7rem", padding: "0.2rem 0.55rem" }}
    >
      <span
        className={`${dot} inline-block flex-shrink-0`}
        style={{ width: 6, height: 6, borderRadius: "50%" }}
      />
      {name}
      <span
        style={{
          fontSize: "0.58rem",
          fontWeight: 700,
          opacity: 0.75,
          letterSpacing: "0.04em",
        }}
      >
        {label}
      </span>
    </span>
  );
}

/* ── Skill gap group ──────────────────────────────────────── */
function SkillGapGroup({
  skills,
  expanded,
  onToggle,
  visibleCount,
}: SkillGapGroupProps) {
  if (skills.length === 0) return null;

  const high = skills.filter((s) => s.importance >= 0.8);
  const med = skills.filter((s) => s.importance >= 0.5 && s.importance < 0.8);
  const low = skills.filter((s) => s.importance < 0.5);

  const visible = expanded ? skills : skills.slice(0, visibleCount);
  const visibleHigh = visible.filter((s) => s.importance >= 0.8);
  const visibleMed = visible.filter(
    (s) => s.importance >= 0.5 && s.importance < 0.8,
  );
  const visibleLow = visible.filter((s) => s.importance < 0.5);
  const hidden = skills.length - visibleCount;
  const skillsToggleText = expanded
    ? "Show less"
    : `+${hidden} more skill${pluralSuffix(hidden)}`;

  return (
    <div className="space-y-3">
      {/* Legend */}
      <div
        className="flex items-center gap-3 flex-wrap color-muted"
        style={{ fontSize: "0.68rem" }}
      >
        {high.length > 0 && (
          <span className="flex items-center gap-1">
            <span
              className="skill-dot-high inline-block"
              style={{ width: 6, height: 6, borderRadius: "50%" }}
            />
            {high.length} High priority
          </span>
        )}
        {med.length > 0 && (
          <span className="flex items-center gap-1">
            <span
              className="skill-dot-med inline-block"
              style={{ width: 6, height: 6, borderRadius: "50%" }}
            />
            {med.length} Medium priority
          </span>
        )}
        {low.length > 0 && (
          <span className="flex items-center gap-1">
            <span
              className="skill-dot-low inline-block"
              style={{ width: 6, height: 6, borderRadius: "50%" }}
            />
            {low.length} Low priority
          </span>
        )}
      </div>

      {/* Grouped badges */}
      <div className="space-y-2">
        {visibleHigh.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {visibleHigh.map((s) => (
              <SkillBadge
                key={s.skill_name}
                name={s.skill_name}
                importance={s.importance}
              />
            ))}
          </div>
        )}
        {visibleMed.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {visibleMed.map((s) => (
              <SkillBadge
                key={s.skill_name}
                name={s.skill_name}
                importance={s.importance}
              />
            ))}
          </div>
        )}
        {visibleLow.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {visibleLow.map((s) => (
              <SkillBadge
                key={s.skill_name}
                name={s.skill_name}
                importance={s.importance}
              />
            ))}
          </div>
        )}
      </div>

      {skills.length > visibleCount && (
        <button
          onClick={onToggle}
          className="text-xs mt-1 flex items-center gap-1 color-muted"
        >
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            fill="none"
            style={{
              transition: "transform 0.2s",
              transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
            }}
          >
            <path
              d="M1.5 3.5l3.5 3.5 3.5-3.5"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {skillsToggleText}
        </button>
      )}
    </div>
  );
}

/* ── Page ─────────────────────────────────────────────────── */
const SKILLS_VISIBLE = 8;

export default function DashboardPage() {
  const { data, loading } = useDashboard();
  const [skillsExpanded, setSkillsExpanded] = useState(false);
  const [rolesExpanded, setRolesExpanded] = useState(false);

  if (loading) return <LoadingSpinner label="Loading dashboard…" />;

  if (!data)
    return (
      <div className="surface-alt rounded-xl text-center py-16 color-muted">
        <p className="text-3xl mb-3">⚠️</p>
        <p className="text-sm">
          Unable to load dashboard data. Please try refreshing.
        </p>
      </div>
    );

  const skillCount = data.skill_distribution.length;
  const gapCount = data.skill_gaps?.missing_skills?.length ?? 0;
  const coverage = data.skill_gaps?.coverage_percent ?? 0;
  const sortedGaps = [...(data.skill_gaps?.per_role ?? [])].sort(
    (a, b) => a.coverage_percent - b.coverage_percent,
  );
  const hiddenRoles = sortedGaps.length - 1;
  const rolesToggleText = rolesExpanded
    ? "Show less"
    : `Show ${hiddenRoles} more role${pluralSuffix(hiddenRoles)}`;

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="anim-fade-up">
        <h1 className="font-display" style={{ marginBottom: "0.25rem" }}>
          Career Overview
        </h1>
        <p className="text-sm color-muted">
          Your personalised skill and job readiness snapshot.
        </p>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <ProgressRing score={data.match_score} />
        <StatCard
          label="Skills Added"
          value={String(skillCount)}
          sub="in your profile"
          color="var(--brand-500)"
        />
        <StatCard
          label="Skill Gaps"
          value={String(gapCount)}
          sub="skills to acquire"
          color={gapCount > 0 ? "var(--warning)" : "var(--success)"}
        />
        <StatCard
          label="Coverage"
          value={`${coverage}%`}
          sub="of required skills"
          color="var(--accent-500)"
        />
      </div>

      {/* Skills */}
      <section className="anim-fade-up delay-1">
        <div className="flex items-center justify-between mb-3">
          <div className="section-label flex items-center gap-2">
            <span>🛠</span> Your Skills
          </div>
          <Link
            href="/dashboard/skills"
            className="text-xs font-medium color-brand"
          >
            Manage →
          </Link>
        </div>
        {skillCount > 0 ? (
          <div className="flex flex-wrap gap-2">
            {data.skill_distribution.map((s, i) => (
              <span
                key={s.skill}
                className="badge badge-brand anim-fade-up"
                style={{ animationDelay: `${i * 0.025}s` }}
              >
                {s.skill}
              </span>
            ))}
          </div>
        ) : (
          <div className="surface-alt rounded-xl px-5 py-6 flex items-center gap-4">
            <span className="text-2xl">🌱</span>
            <div>
              <p
                className="text-sm font-medium color-primary"
                style={{ margin: 0 }}
              >
                No skills yet
              </p>
              <Link href="/dashboard/skills" className="text-xs color-brand">
                Add your first skill →
              </Link>
            </div>
          </div>
        )}
      </section>

      {/* Top roles */}
      {data.top_roles?.length > 0 && (
        <section className="anim-fade-up delay-2">
          <div className="flex items-center justify-between mb-3">
            <div className="section-label flex items-center gap-2">
              <span>🗺</span> Top Recommended Roles
            </div>
            <Link
              href="/dashboard/roles"
              className="text-xs font-medium color-brand"
            >
              View all →
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.top_roles.map((r, i) => {
              const pct = Math.round(r.match_score * 100);
              const barColor = getScoreColor(pct);
              return (
                <Link
                  key={r.id}
                  href={`/dashboard/roles?id=${r.id}`}
                  className={`card role-card-link anim-fade-up delay-${Math.min(i, 3)}`}
                >
                  <h3 className="text-sm font-semibold role-title">
                    {r.title}
                  </h3>
                  <div className="flex justify-between text-xs mb-1 color-muted">
                    <span>Match</span>
                    <span style={{ color: barColor, fontWeight: 600 }}>
                      {pct}%
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden match-bar-track">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${pct}%`,
                        background: barColor,
                        transition: "width 0.6s ease",
                      }}
                    />
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* Skill gaps by role */}
      {sortedGaps.length > 0 && (
        <section className="anim-fade-up delay-2">
          <div className="section-label flex items-center gap-2 mb-3">
            <span>⚡</span> Skill Gaps by Role{" "}
            <span
              className="ml-1 badge skill-badge-med"
              style={{ fontSize: "0.7rem" }}
            >
              {gapCount} missing overall
            </span>
          </div>
          <div className="space-y-3">
            {/* Top priority gap */}
            {(() => {
              const roleGap = sortedGaps[0];
              const skills = roleGap.learning_priority?.length
                ? roleGap.learning_priority
                : roleGap.missing_skills.map((s) => ({
                    skill_name: s,
                    importance: 0.5,
                  }));
              return (
                <div
                  key={roleGap.role_id}
                  className="card card-sm anim-fade-up delay-1 gap-top-card"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="gap-priority-pill">TOP PRIORITY</span>
                      <h3
                        className="text-sm font-semibold color-primary"
                        style={{ margin: 0 }}
                      >
                        {roleGap.role_title}
                      </h3>
                    </div>
                    <span
                      className="text-xs font-semibold"
                      style={{
                        color: getCoverageColor(roleGap.coverage_percent),
                      }}
                    >
                      {roleGap.coverage_percent}% covered
                    </span>
                  </div>
                  {roleGap.missing_skills.length === 0 ? (
                    <p className="text-xs color-success">
                      ✓ You have all required skills
                    </p>
                  ) : (
                    <SkillGapGroup
                      skills={skills}
                      expanded={skillsExpanded}
                      onToggle={() => setSkillsExpanded((p) => !p)}
                      visibleCount={SKILLS_VISIBLE}
                    />
                  )}
                </div>
              );
            })()}

            {/* Remaining gaps */}
            {sortedGaps.length > 1 && (
              <>
                {rolesExpanded &&
                  sortedGaps.slice(1).map((roleGap, ri) => (
                    <div
                      key={roleGap.role_id}
                      className={`card card-sm anim-fade-up delay-${Math.min(ri + 1, 5)}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3
                          className="text-sm font-semibold color-primary"
                          style={{ margin: 0 }}
                        >
                          {roleGap.role_title}
                        </h3>
                        <span
                          className="text-xs font-semibold"
                          style={{
                            color: getCoverageColor(roleGap.coverage_percent),
                          }}
                        >
                          {roleGap.coverage_percent}% covered
                        </span>
                      </div>
                      {roleGap.missing_skills.length === 0 ? (
                        <p className="text-xs color-success">
                          ✓ You have all required skills
                        </p>
                      ) : (
                        <SkillGapGroup
                          skills={
                            roleGap.learning_priority?.length
                              ? roleGap.learning_priority
                              : roleGap.missing_skills.map((s) => ({
                                  skill_name: s,
                                  importance: 0.5,
                                }))
                          }
                          expanded
                          onToggle={() => {}}
                          visibleCount={Infinity}
                        />
                      )}
                    </div>
                  ))}
                <button
                  onClick={() => setRolesExpanded((p) => !p)}
                  className="show-more-btn flex items-center gap-1.5 text-xs font-medium w-full justify-center py-2 rounded-lg transition-all color-muted"
                >
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 12 12"
                    fill="none"
                    style={{
                      transition: "transform 0.2s",
                      transform: rolesExpanded
                        ? "rotate(180deg)"
                        : "rotate(0deg)",
                    }}
                  >
                    <path
                      d="M2 4l4 4 4-4"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  {rolesToggleText}
                </button>
              </>
            )}
          </div>
        </section>
      )}

      {/* Learning + Jobs */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Learning plan */}
        <section className="anim-fade-up delay-3">
          <div className="section-label flex items-center gap-2 mb-3">
            <span>📚</span> Learning Recommendations
          </div>
          {data.learning_plan?.length > 0 ? (
            <div className="space-y-2">
              {data.learning_plan.slice(0, 7).map((c) => (
                <a
                  key={c.id}
                  href={c.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card card-xs flex items-start gap-3 group no-underline"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm icon-box-brand">
                    🎓
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3
                      className="text-sm font-medium truncate color-primary"
                      style={{ margin: 0 }}
                    >
                      {c.title}
                    </h3>
                    <p className="text-xs mt-0.5 truncate color-muted">
                      {c.provider} · {c.matched_skills.join(", ")}
                    </p>
                  </div>
                  <span className="list-item-arrow flex-shrink-0 text-xs transition-transform group-hover:translate-x-0.5">
                    →
                  </span>
                </a>
              ))}
            </div>
          ) : (
            <div className="surface-alt rounded-xl text-center py-8 color-muted">
              <p className="text-2xl mb-2">📚</p>
              <p className="text-sm">No course recommendations yet.</p>
              <p className="text-xs mt-1">
                Add skills or upload your resume to get learning suggestions.
              </p>
            </div>
          )}
        </section>

        {/* Job matches */}
        {data.job_matches?.length > 0 && (
          <section className="anim-fade-up delay-4">
            <div className="flex items-center justify-between mb-3">
              <div className="section-label flex items-center gap-2">
                <span>💼</span> Job Matches
              </div>
              <Link
                href="/dashboard/jobs"
                className="text-xs font-medium color-brand"
              >
                View all →
              </Link>
            </div>
            <div className="space-y-2">
              {data.job_matches.map((j) => (
                <a
                  key={j.id}
                  href={j.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card card-xs flex items-start gap-3 group no-underline"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold icon-box-accent">
                    {j.company.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3
                      className="text-sm font-medium truncate color-primary"
                      style={{ margin: 0 }}
                    >
                      {j.title}
                    </h3>
                    <p className="text-xs mt-0.5 truncate color-muted">
                      {j.company}
                      {j.location ? " · " + j.location : ""}
                    </p>
                  </div>
                  <span className="list-item-arrow flex-shrink-0 text-xs transition-transform group-hover:translate-x-0.5">
                    →
                  </span>
                </a>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
