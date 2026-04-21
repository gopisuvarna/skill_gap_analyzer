"use client";

import { useSettings } from "@/hooks/useSettings";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export default function SettingsPage() {
  const { user, loading, logoutLoading, handleLogout } = useSettings();

  if (loading) return <LoadingSpinner label="Loading settings…" />;

  const initials = user?.email ? user.email.slice(0, 2).toUpperCase() : "??";

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="font-display" style={{ marginBottom: "0.35rem" }}>
          Settings
        </h1>
        <p className="text-sm color-muted">
          Manage your account and preferences.
        </p>
      </div>

      
      <div className="card card-md anim-fade-up">
        <p className="section-label">Account Details</p>

        <div className="flex items-center gap-4 mb-5">
          <div className="w-14 h-14 rounded-xl flex items-center justify-center text-lg font-bold flex-shrink-0 settings-avatar">
            {initials}
          </div>
          <div>
            <p
              className="font-semibold text-base color-primary"
              style={{ margin: 0 }}
            >
              {user?.email}
            </p>
          </div>
        </div>

        <div className="space-y-0.5">
          {[
            { label: "Email", value: user?.email },
{
              label: "Account ID",
              value: (
                <code className="text-xs font-mono color-muted">
                  {user?.id || "—"}
                </code>
              ),
            },
          ].map((row) => (
            <div
              key={row.label}
              className="lflex justify-between items-center py-3 settings-row"
            >
              <span className="text-sm color-muted">{row.label}</span>
              <span className="text-sm font-medium color-primary">
                {row.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      
      <div className="card card-md anim-fade-up delay-1 settings-danger-card">
        <p className="section-label color-error">Session</p>
        <div className="flex items-center justify-between gap-4">
          <div>
            <p
              className="font-medium text-sm color-primary"
              style={{ margin: "0 0 0.2rem" }}
            >
              Sign Out
            </p>
            <p className="text-xs color-muted">
              You'll be redirected to the login page.
            </p>
          </div>
          <button
            onClick={handleLogout}
            disabled={logoutLoading}
            className="btn btn-danger flex-shrink-0"
          >
            {logoutLoading ? "Signing out…" : "Logout"}
          </button>
        </div>
      </div>
    </div>
  );
}
