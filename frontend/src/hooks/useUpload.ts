import { useState } from "react";
import { api } from "@/lib/api";
import { useUploadResult } from "../../app/dashboard/upload-result-context";
export function useUpload() {
  const { setUploadResult } = useUploadResult();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [success, setSuccess] = useState<boolean>(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const chosen = e.target.files?.[0];
    if (!chosen) return;
    if (!chosen.name.toLowerCase().endsWith(".pdf")) {
      setMessage("Please select a PDF file only.");
      setFile(null);
      return;
    }
    setFile(chosen);
    setMessage("");
    setSuccess(false);
  }

  async function handleUpload() {
    if (!file) {
      setMessage("Please select a PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("Uploading & extracting skills…");

      const response = await api.post("/documents/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = response.data;
      setUploadResult({
        all_skills: data.all_skills || [],
        rule_based_skills: data.rule_based_skills || [],
        llm_skills: data.llm_skills || [],
        recommended_roles: data.recommended_roles || [],
      });

      setMessage("Upload successful! Skills and roles have been extracted.");
      setSuccess(true);
    } catch (error: unknown) {
      const err = error as { response?: { data?: { error?: string } } };
      setMessage(
        err.response?.data?.error || "Upload failed. Please try again.",
      );
      setSuccess(false);
    } finally {
      setLoading(false);
    }
  }

  return { file, loading, message, success, handleFileChange, handleUpload };
}
