"use client";

import { useUploadResult } from "../upload-result-context";
import { useRoles } from "@/hooks/useRoles";
import { LoadingSpinner } from "@/components/LoadingSpinner";
function getMatchColor(pct: number): string {
  if (pct >= 80) return "var(--success)";
  if (pct >= 55) return "var(--brand-500)";
  return "var(--warning)";
}
interface MatchBarProps {
  readonly score: number;
}

function MatchBar({ score }: MatchBarProps) {
  const pct = Math.round(score * 100);
  const color = getMatchColor(pct); // S3358: no nested ternary here anymore
  return (
    <div className="mt-3">
      <div className="flex justify-between text-xs mb-1 color-muted">
        <span>Match</span>
        <span className="font-semibold" style={{ color }}>
          {pct}%
        </span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden match-bar-track">
        <div
          className="h-full rounded-full"
          style={{
            width: `${pct}%`,
            background: color,
            transition: "width 0.6s ease",
          }}
        />
      </div>
    </div>
  );
}

export default function RolesPage() {
  const { uploadResult } = useUploadResult();
  const { roles, fromResume, loading } = useRoles(
    uploadResult?.recommended_roles ?? [],
  );

  if (loading) return <LoadingSpinner label="Loading roles…" />;

  return (
    <div className="space-y-10">
      
      <div>
        <h1 className="font-display" style={{ marginBottom: "0.35rem" }}>
          Recommended Roles
        </h1>
        <p className="text-sm color-muted">
          Based on your skills and resume analysis.
        </p>
      </div>

      
      {fromResume.length > 0 && (
        <section className="anim-fade-up">
          <div className="section-label flex items-center gap-2 mb-3">
            <span>📄</span> From your resume
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {fromResume.map((r, i) => (
              <div
                key={r.role}
                className={`card card-sm anim-fade-up delay-${Math.min(i + 1, 5)}`}
              >
                <h3
                  className="text-sm font-semibold color-primary"
                  style={{ margin: "0 0 0.25rem" }}
                >
                  {r.role}
                </h3>
                {r.description && (
                  <p
                    className="text-xs line-clamp-2 color-muted"
                    style={{ lineHeight: 1.55 }}
                  >
                    {r.description}
                  </p>
                )}
                {r.skills && (
                  <p className="text-xs mt-2 line-clamp-1 color-brand">
                    {r.skills}
                  </p>
                )}
                {r.score != null && <MatchBar score={r.score} />}
              </div>
            ))}
          </div>
        </section>
      )}

      
      <section className="anim-fade-up delay-2">
        <div className="section-label flex items-center gap-2 mb-3">
          <span>👤</span> Based on your profile
        </div>
        {roles.length === 0 ? (
          <div className="surface-alt text-center py-12 rounded-xl color-muted">
            <p className="text-sm">
              No role recommendations yet. Add skills or upload your resume to
              get started.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {roles.map((r, i) => (
              <div
                key={r.id}
                className={`card card-sm anim-fade-up delay-${Math.min(i + 1, 5)}`}
              >
                <h3
                  className="text-sm font-semibold color-primary"
                  style={{ margin: "0 0 0.25rem" }}
                >
                  {r.title}
                </h3>
                {r.description && (
                  <p
                    className="text-xs line-clamp-2 color-muted"
                    style={{ lineHeight: 1.55 }}
                  >
                    {r.description}
                  </p>
                )}
                {r.match_score != null && <MatchBar score={r.match_score} />}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
