"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { isLikelyEmail } from "@/lib/validation";
import { AuthLayout, AuthSubmitButton } from "@/components/AuthLayout";

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
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to your account"
      serverError={serverError}
      footerPrompt="No account yet?"
      footerHref="/register"
      footerLinkText="Create one"
      blobVariant="login"
    >
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
        <AuthSubmitButton
          loading={loading}
          loadingText="Signing in..."
          idleText="Sign In"
        />
      </form>
    </AuthLayout>
  );
}
