"use client";
import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useMemo } from "react";
export interface RecommendedRole {
  role: string;
  description: string;
  skills: string;
  score: number;
}
export interface UploadResult {
  all_skills: string[];
  rule_based_skills: string[];
  llm_skills: string[];
  recommended_roles: RecommendedRole[];
}

interface UploadResultContextValue {

  uploadResult: UploadResult | null;

  setUploadResult: (result: UploadResult | null) => void;

  clearUploadResult: () => void;
}
const UploadResultContext = createContext<UploadResultContextValue | null>(
  null,
);
type UploadResultProviderProps = Readonly<{ children: ReactNode }>;

export function UploadResultProvider({ children }: UploadResultProviderProps) {
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const updateUploadResult = useCallback((result: UploadResult | null) => {
    setUploadResult(result);
  }, []);
  const clearUploadResult = useCallback(() => setUploadResult(null), []);

  const contextValue = useMemo(
    () => ({
      uploadResult,
      setUploadResult: updateUploadResult,
      clearUploadResult,
    }),
    [uploadResult, updateUploadResult, clearUploadResult],
  );
  return (
    <UploadResultContext.Provider value={contextValue}>
      {children}
    </UploadResultContext.Provider>
  );
}
export function useUploadResult() {
  const ctx = useContext(UploadResultContext);
  if (!ctx)
    throw new Error("useUploadResult must be used within UploadResultProvider");
  return ctx;
}
