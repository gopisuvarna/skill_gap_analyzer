"use client";

import Link from "next/link";
import { useUpload } from "@/hooks/useUpload";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export default function DocumentsPage() {
  const { file, loading, message, success, handleFileChange, handleUpload } =
    useUpload();

  return (
    <div className="max-w-2xl mx-auto">
      
      <div className="mb-8">
        <h1 className="font-display" style={{ marginBottom: "0.35rem" }}>
          Upload Resume
        </h1>
        <p className="text-sm color-muted">
          PDF format only — we'll extract your skills and suggest matching
          roles.
        </p>
      </div>

      <div className="card card-auth">
        
        <label
          htmlFor="resume-upload"
          className={`flex flex-col items-center justify-center gap-3 w-full rounded-xl py-10 px-6 cursor-pointer transition-all dropzone ${file ? "dropzone-active" : ""}`}
        >
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${file ? "dropzone-icon-active" : "dropzone-icon-idle"}`}
          >
            {file ? "📄" : "☁️"}
          </div>

          {file ? (
            <>
              <p className="font-medium text-sm color-brand-600">{file.name}</p>
              <p className="text-xs color-muted">
                {(file.size / 1024).toFixed(1)} KB · Click to change
              </p>
            </>
          ) : (
            <>
              <p className="font-medium text-sm color-primary">
                Click to browse or drag & drop
              </p>
              <p className="text-xs color-muted">PDF files only</p>
            </>
          )}

          <input
            id="resume-upload"
            type="file"
            accept="application/pdf,.pdf"
            onChange={handleFileChange}
            className="sr-only"
          />
        </label>

        
        <button
          onClick={handleUpload}
          disabled={loading || !file}
          className="btn btn-primary w-full mt-5"
        >
          {loading ? (
            <LoadingSpinner label="Processing…" />
          ) : (
            "Upload & Extract Skills"
          )}
        </button>

        
        {message && (
          <div
            className={`mt-4 px-4 py-3 rounded-lg text-sm ${success ? "upload-msg-success" : "upload-msg-error"}`}
          >
            {message}
          </div>
        )}

        
        {success && (
          <div
            className="mt-5 pt-4 flex flex-col sm:flex-row gap-3"
            style={{ borderTop: "1px solid var(--border-subtle)" }}
          >
            <Link
              href="/dashboard/skills"
              className="btn btn-secondary flex-1 justify-center text-sm"
            >
              View Extracted Skills →
            </Link>
            <Link
              href="/dashboard/roles"
              className="btn btn-secondary flex-1 justify-center text-sm"
            >
              View Recommended Roles →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
