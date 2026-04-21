"use client";

import { useJobs } from "@/hooks/useJobs";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import type { Job } from "@/hooks/useJobs";
function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) =>
    n >= 100_000
      ? `₹${(n / 100_000).toFixed(0)}L`
      : `₹${(n / 1000).toFixed(0)}K`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  return `Up to ${fmt(max!)}`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const h = Math.floor(diff / 3_600_000);
  if (h < 1) return "Just now";
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d === 1) return "Yesterday";
  if (d < 30) return `${d}d ago`;
  return `${Math.floor(d / 30)}mo ago`;
}
function getMatchColor(pct: number): string {
  if (pct >= 70) return "var(--success)";
  if (pct >= 40) return "var(--brand-500)";
  return "var(--warning)";
}
function getEmptyDescription(tab: "matched" | "all", search: string): string {
  if (tab === "matched")
    return "Upload your resume or add skills to see matches.";
  if (search) return "Try a different search term.";
  return "Jobs will appear after the next sync.";
}
interface JobCardProps {
  readonly job: Job;
  readonly showMatch?: boolean;
}

function JobCard({ job, showMatch }: JobCardProps) {
  const salary = formatSalary(job.salary_min, job.salary_max);
  const matchPct =
    showMatch && job.skills.length > 0
      ? Math.round((job.matched_skills.length / job.skills.length) * 100)
      : null;

  const matchColor = matchPct === null ? undefined : getMatchColor(matchPct);

  return (
    <a
      href={job.url}
      target="_blank"
      rel="noopener noreferrer"
      className="card group flex items-start gap-4 no-underline"
      style={{ padding: "1rem 1.25rem" }}
    >
      <div className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold icon-box-brand">
        {(job.company || "?").slice(0, 2).toUpperCase()}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <h3
            className="text-sm font-semibold color-primary"
            style={{ margin: 0 }}
          >
            {job.title}
          </h3>
          <span
            className="flex-shrink-0 text-sm color-muted transition-transform group-hover:translate-x-0.5"
            style={{ marginTop: "2px" }}
          >
            →
          </span>
        </div>

        <p className="text-xs mt-0.5 color-muted">
          {job.company}
          {job.location ? ` · ${job.location}` : ""}
          {salary && (
            <span className="ml-2 px-1.5 py-0.5 rounded text-xs font-medium job-salary-tag">
              {salary}
            </span>
          )}
          <span className="ml-2 color-muted">·</span>
          <span className="ml-2">{timeAgo(job.posted_at)}</span>
        </p>

        {showMatch && matchPct !== null && (
          <div className="mt-2">
            <div className="flex justify-between text-xs mb-1 color-muted">
              <span>Skill match</span>
              
              <span className="font-semibold" style={{ color: matchColor }}>
                {matchPct}%
              </span>
            </div>
            <div className="h-1.5 rounded-full overflow-hidden match-bar-track">
              
              <div
                className="h-full rounded-full"
                style={{
                  width: `${matchPct}%`,
                  background: matchColor,
                  transition: "width 0.6s ease",
                }}
              />
            </div>
          </div>
        )}

        {showMatch && job.matched_skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {job.matched_skills.slice(0, 5).map((s) => (
              <span
                key={s}
                className="badge badge-accent"
                style={{ fontSize: "0.68rem", padding: "0.1rem 0.45rem" }}
              >
                {s}
              </span>
            ))}
            {job.matched_skills.length > 5 && (
              <span
                className="badge badge-brand"
                style={{ fontSize: "0.68rem", padding: "0.1rem 0.45rem" }}
              >
                +{job.matched_skills.length - 5}
              </span>
            )}
          </div>
        )}
      </div>
    </a>
  );
}
interface SearchBarProps {
  readonly value: string;
  readonly onChange: (v: string) => void;
}

function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm color-muted">
        🔍
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search by title or company…"
        className="w-full rounded-xl text-sm search-field"
        style={{ paddingLeft: "2.25rem" }}
      />
    </div>
  );
}
interface StatsTextProps {
  readonly stats: ReturnType<typeof useJobs>["stats"];
}

function StatsText({ stats }: StatsTextProps) {
  if (!stats) return <>Curated for your skill profile.</>;
  return (
    <>
      <span className="font-medium color-primary">
        {stats.total_jobs.toLocaleString()}
      </span>{" "}
      open positions
      {stats.matched_count > 0 && (
        <>
          {" "}
          ·{" "}
          <span className="font-medium color-brand">
            {stats.matched_count}
          </span>{" "}
          match your skills
        </>
      )}
      {stats.last_synced && <> · Updated {timeAgo(stats.last_synced)}</>}
    </>
  );
}
interface EmptyStateProps {
  readonly tab: "matched" | "all";
  readonly search: string;
}

function EmptyState({ tab, search }: EmptyStateProps) {
  const title = tab === "matched" ? "No matched jobs yet" : "No jobs found";
  const description = getEmptyDescription(tab, search);
  return (
    <div className="surface-alt rounded-xl text-center py-14">
      <p className="text-3xl mb-3">💼</p>
      <p className="text-sm font-medium color-primary">{title}</p>
      <p className="text-xs mt-1 color-muted">{description}</p>
    </div>
  );
}

interface PaginationProps {
  readonly page: number;
  readonly totalPages: number;
  readonly setPage: React.Dispatch<React.SetStateAction<number>>;
}

function Pagination({ page, totalPages, setPage }: PaginationProps) {
  return (
    <div className="flex items-center justify-between pt-2">
      <button
        onClick={() => setPage((p) => Math.max(1, p - 1))}
        disabled={page === 1}
        className={`text-xs px-3 py-1.5 rounded-lg ${page === 1 ? "pagination-btn-disabled" : "pagination-btn"}`}
      >
        ← Prev
      </button>
      <span className="text-xs color-muted">
        Page {page} of {totalPages}
      </span>
      <button
        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        disabled={page === totalPages}
        className={`text-xs px-3 py-1.5 rounded-lg ${page === totalPages ? "pagination-btn-disabled" : "pagination-btn"}`}
      >
        Next →
      </button>
    </div>
  );
}
interface JobsContentProps {
  readonly loading: boolean;
  readonly displayJobs: Job[];
  readonly tab: "matched" | "all";
  readonly search: string;
}

function JobsContent({ loading, displayJobs, tab, search }: JobsContentProps) {
  if (loading) return <LoadingSpinner label="Loading jobs…" />;
  if (displayJobs.length === 0) return <EmptyState tab={tab} search={search} />;
  return (
    <div className="space-y-3">
      {displayJobs.map((j, i) => (
        <div key={j.id} className={`anim-fade-up delay-${Math.min(i + 1, 5)}`}>
          <JobCard job={j} showMatch={tab === "matched"} />
        </div>
      ))}
    </div>
  );
}
export default function JobsPage() {
  const {
    matched,
    stats,
    loading,
    refreshing,
    search,
    setSearch,
    page,
    setPage,
    total,
    totalPages,
    tab,
    setTab,
    displayJobs,
    handleRefresh,
  } = useJobs();

  return (
    <div className="space-y-6 max-w-3xl">
      
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display" style={{ marginBottom: "0.25rem" }}>
            Jobs
          </h1>
          <p className="text-sm color-muted">
            <StatsText stats={stats} />
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="refresh-btn flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg"
          style={{
            cursor: refreshing ? "wait" : "pointer",
            opacity: refreshing ? 0.6 : 1,
          }}
        >
          <span
            style={{
              display: "inline-block",
              animation: refreshing ? "spin 1s linear infinite" : "none",
            }}
          >
            ↻
          </span>
          {refreshing ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      <SearchBar value={search} onChange={setSearch} />

      
      <div className="flex gap-2">
        {(["matched", "all"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`text-sm px-4 py-1.5 rounded-lg font-medium ${tab === t ? "tab-btn-active" : "tab-btn"}`}
          >
            {t === "matched"
              ? `✦ Matched (${matched.length})`
              : `All jobs (${total})`}
          </button>
        ))}
      </div>

      
      <JobsContent
        loading={loading}
        displayJobs={displayJobs}
        tab={tab}
        search={search}
      />

      
      {tab === "all" && totalPages > 1 && (
        <Pagination page={page} totalPages={totalPages} setPage={setPage} />
      )}
    </div>
  );
}
