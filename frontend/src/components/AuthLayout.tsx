import Link from "next/link";
import React from "react";

type BlobVariant = "login" | "register";

interface AuthLayoutProps {
  readonly title: string;
  readonly subtitle: string;
  readonly serverError?: string;
  readonly footerPrompt: string;
  readonly footerHref: string;
  readonly footerLinkText: string;
  readonly blobVariant: BlobVariant;
  readonly children: React.ReactNode;
}

function BlobBackground({
  blobVariant,
}: {
  readonly blobVariant: BlobVariant;
}) {
  if (blobVariant === "register") {
    return (
      <div
        className="absolute inset-0 pointer-events-none overflow-hidden"
        aria-hidden="true"
      >
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full auth-bg-blob-1" />
        <div className="absolute -bottom-32 -right-32 w-80 h-80 rounded-full auth-bg-blob-2" />
      </div>
    );
  }

  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden"
      aria-hidden="true"
    >
      <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full auth-bg-blob-1" />
      <div className="absolute -bottom-32 -left-32 w-80 h-80 rounded-full auth-bg-blob-2" />
    </div>
  );
}

export function AuthLayout({
  title,
  subtitle,
  serverError,
  footerPrompt,
  footerHref,
  footerLinkText,
  blobVariant,
  children,
}: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <BlobBackground blobVariant={blobVariant} />

      <div className="relative z-10 w-full max-w-md anim-fade-up">
        <div className="flex justify-center mb-8">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold auth-logo">
            S
          </div>
        </div>

        <div className="card card-auth">
          <h1 className="text-2xl mb-1 font-display">{title}</h1>
          <p className="text-sm mb-8 color-muted">{subtitle}</p>

          {serverError && (
            <div className="mb-5 px-4 py-3 rounded-lg text-sm font-medium auth-error">
              {serverError}
            </div>
          )}

          {children}
        </div>

        <p className="text-center text-sm mt-5 color-muted">
          {footerPrompt}{" "}
          <Link href={footerHref} className="font-medium color-brand">
            {footerLinkText}
          </Link>
        </p>
      </div>
    </div>
  );
}

interface AuthSubmitButtonProps {
  readonly loading: boolean;
  readonly loadingText: string;
  readonly idleText: string;
}

export function AuthSubmitButton({
  loading,
  loadingText,
  idleText,
}: AuthSubmitButtonProps) {
  return (
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
          {loadingText}
        </span>
      ) : (
        idleText
      )}
    </button>
  );
}
