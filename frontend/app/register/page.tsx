"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

function isLikelyEmail(value: string): boolean {
  const v = value.trim();
  if (!v || v.includes(" ")) return false;
  const at = v.indexOf("@");
  if (at <= 0 || at !== v.lastIndexOf("@") || at === v.length - 1) return false;
  const domain = v.slice(at + 1);
  const dot = domain.indexOf(".");
  return dot > 0 && dot < domain.length - 1;
}

const MIN_PASSWORD = 8;

export default function RegisterPage() {
  const router = useRouter();
  const emailInputRef = useRef<HTMLInputElement | null>(null);
  const passwordInputRef = useRef<HTMLInputElement | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>(
    {},
  );
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);

  // FIX: validate fields before hitting the API
  function validate(): boolean {
    const next: typeof errors = {};
    if (!email.trim()) next.email = "Email is required.";
    else if (!isLikelyEmail(email)) next.email = "Enter a valid email address.";
    if (!password) next.password = "Password is required.";
    else if (password.length < MIN_PASSWORD)
      next.password = `Password must be at least ${MIN_PASSWORD} characters.`;
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setServerError("");
    if (!validate()) {
      if (!email.trim()) {
        emailInputRef.current?.focus();
      } else if (!password) {
        passwordInputRef.current?.focus();
      }
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/register/", { email, password });
      router.push("/login");
      router.refresh();
    } catch (err: unknown) {
      const res = (err as { response?: { data?: Record<string, string[]> } })
        ?.response?.data;
      const msg =
        typeof res?.detail === "string"
          ? res.detail
          : res?.email?.[0] || res?.password?.[0] || "Registration failed";
      setServerError(msg);
    } finally {
      setLoading(false);
    }
  }

  // FIX: live password strength indicator
  let strength: "weak" | "fair" | "strong" | null = null;
  if (password.length > 0 && password.length < 8) {
    strength = "weak";
  } else if (password.length < 12 && password.length > 0) {
    strength = "fair";
  } else if (password.length >= 12) {
    strength = "strong";
  }

  const strengthLabel = { weak: "Weak", fair: "Fair", strong: "Strong" };
  const strengthColor = {
    weak: "var(--error)",
    fair: "var(--warning)",
    strong: "var(--success)",
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Background blobs */}
      <div
        className="absolute inset-0 pointer-events-none overflow-hidden"
        aria-hidden="true"
      >
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full auth-bg-blob-1" />
        <div className="absolute -bottom-32 -right-32 w-80 h-80 rounded-full auth-bg-blob-2" />
      </div>

      <div className="relative z-10 w-full max-w-md anim-fade-up">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold auth-logo">
            S
          </div>
        </div>

        <div className="card card-auth">
          <h1 className="text-2xl mb-1 font-display">Create account</h1>
          <p className="text-sm mb-8 color-muted">
            Start your career intelligence journey
          </p>

          {serverError && (
            <div className="mb-5 px-4 py-3 rounded-lg text-sm font-medium auth-error">
              {serverError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label
                htmlFor="register-email"
                className="block text-sm font-medium mb-1.5 form-label"
              >
                Email address
              </label>
              <input
                ref={emailInputRef}
                id="register-email"
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setErrors((p) => ({ ...p, email: undefined }));
                }}
                className={`input ${errors.email ? "input-error" : ""}`}
              />
              {errors.email && (
                <p className="text-xs mt-1 color-error">{errors.email}</p>
              )}
            </div>

            <div>
              <label
                htmlFor="register-password"
                className="block text-sm font-medium mb-1.5 form-label"
              >
                Password{" "}
                <span className="ml-1 font-normal color-muted">
                  (min {MIN_PASSWORD} characters)
                </span>
              </label>
              <input
                ref={passwordInputRef}
                id="register-password"
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setErrors((p) => ({ ...p, password: undefined }));
                }}
                className={`input ${errors.password ? "input-error" : ""}`}
              />
              {/* FIX: live password strength bar */}
              {strength && (
                <div className="mt-1.5">
                  <div className="flex gap-1 mb-1">
                    {(["weak", "fair", "strong"] as const).map((lvl) => (
                      <div
                        key={lvl}
                        className="h-1 flex-1 rounded-full transition-all"
                        style={{
                          background:
                            ["weak", "fair", "strong"].indexOf(lvl) <=
                            ["weak", "fair", "strong"].indexOf(strength)
                              ? strengthColor[strength]
                              : "var(--border-subtle)",
                        }}
                      />
                    ))}
                  </div>
                  <p
                    className="text-xs"
                    style={{ color: strengthColor[strength] }}
                  >
                    {strengthLabel[strength]} password
                  </p>
                </div>
              )}
              {errors.password && (
                <p className="text-xs mt-1 color-error">{errors.password}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="animate-spin w-4 h-4"
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
                  Creating account…
                </span>
              ) : (
                "Create Account"
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-sm mt-5 color-muted">
          Have an account?{" "}
          <Link href="/login" className="font-medium color-brand">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
