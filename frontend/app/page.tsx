"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
// defines the home page component and created router instance for navigation
export default function Home() {
  const router = useRouter();
  // checks for the presence of an access token in the cookies and redirects to the dashboard if found
  useEffect(() => {
    const token = document.cookie.includes("access_token");
    if (token) router.replace("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-16 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div
          className="absolute -top-32 -left-32 w-96 h-96 rounded-full"
          style={{
            background:
              "radial-gradient(circle, rgba(110,127,213,0.12) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute -bottom-24 -right-24 w-80 h-80 rounded-full"
          style={{
            background:
              "radial-gradient(circle, rgba(52,201,174,0.10) 0%, transparent 70%)",
          }}
        />
      </div>

      <div className="relative z-10 text-center max-w-2xl mx-auto anim-fade-up">
        {/* Eyebrow */}
        <span
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold tracking-widest uppercase mb-6"
          style={{
            background: "var(--brand-50)",
            color: "var(--brand-600)",
            border: "1.5px solid var(--brand-200)",
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full inline-block"
            style={{ background: "var(--accent-400)" }}
          />{" "}
          AI-Powered Career Platform
        </span>

        {/* Heading */}
        <h1
          className="mb-4"
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 700,
            color: "var(--text-primary)",
          }}
        >
          AI{" "}
          <span
            style={{
              background:
                "linear-gradient(135deg, var(--brand-500) 0%, var(--accent-400) 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Skill Sync
          </span>
        </h1>

        <p
          className="text-lg mb-10 max-w-lg mx-auto"
          style={{ color: "var(--text-secondary)", lineHeight: 1.7 }}
        >
          Identify skill gaps, explore career paths, and measure your job
          readiness — all in one intelligent platform.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/login" className="btn btn-primary text-base px-8">
            Sign In
          </Link>
          <Link href="/register" className="btn btn-secondary text-base px-8">
            Create Account
          </Link>
        </div>

        {/* Feature highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-16">
          {[
            { icon: "🎯", label: "Skill Gap Analysis" },
            { icon: "🗺️", label: "Career Path Mapping" },
            { icon: "✅", label: "Job Readiness Score" },
          ].map((item, i) => (
            <div
              key={item.label}
              className={`card text-center py-5 anim-fade-up delay-${i + 2}`}
              style={{ padding: "1.25rem 1rem" }}
            >
              <div className="text-2xl mb-2">{item.icon}</div>
              <p
                className="text-sm font-medium"
                style={{ color: "var(--text-primary)" }}
              >
                {item.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
