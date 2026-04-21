"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { isLikelyEmail } from "@/lib/validation";
import { AuthLayout, AuthSubmitButton } from "@/components/AuthLayout";

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
    <AuthLayout
      title="Create account"
      subtitle="Start your career intelligence journey"
      serverError={serverError}
      footerPrompt="Have an account?"
      footerHref="/login"
      footerLinkText="Sign in"
      blobVariant="register"
    >
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
              <p className="text-xs" style={{ color: strengthColor[strength] }}>
                {strengthLabel[strength]} password
              </p>
            </div>
          )}
          {errors.password && (
            <p className="text-xs mt-1 color-error">{errors.password}</p>
          )}
        </div>
        <AuthSubmitButton
          loading={loading}
          loadingText="Creating account..."
          idleText="Create Account"
        />
      </form>
    </AuthLayout>
  );
}
