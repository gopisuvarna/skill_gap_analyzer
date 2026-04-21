"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { isLikelyEmail } from "@/lib/validation";

export default function LoginPage() {
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
      await api.post("/auth/login/", { email, password });
      router.push("/dashboard");
      router.refresh();
    } catch (err: unknown) {
      setServerError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Login failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Background blobs */}
      <div
        className="absolute inset-0 pointer-events-none overflow-hidden"
        aria-hidden="true"
      >
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full auth-bg-blob-1" />
        <div className="absolute -bottom-32 -left-32 w-80 h-80 rounded-full auth-bg-blob-2" />
      </div>

      <div className="relative z-10 w-full max-w-md anim-fade-up">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold auth-logo">
            S
          </div>
        </div>

        <div className="card card-auth">
          <h1 className="text-2xl mb-1 font-display">Welcome back</h1>
          <p className="text-sm mb-8 color-muted">Sign in to your account</p>

          {serverError && (
            <div className="mb-5 px-4 py-3 rounded-lg text-sm font-medium auth-error">
              {serverError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label
                htmlFor="login-email"
                className="block text-sm font-medium mb-1.5 form-label"
              >
                Email address
              </label>
              <input
                ref={emailInputRef}
                id="login-email"
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
                htmlFor="login-password"
                className="block text-sm font-medium mb-1.5 form-label"
              >
                Password
              </label>
              <input
                ref={passwordInputRef}
                id="login-password"
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
                  Signing in…
                </span>
              ) : (
                "Sign In"
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-sm mt-5 color-muted">
          No account yet?{" "}
          <Link href="/register" className="font-medium color-brand">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
