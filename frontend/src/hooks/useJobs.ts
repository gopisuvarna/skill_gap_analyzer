import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api";

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  salary_min: number | null;
  salary_max: number | null;
  skills: string[];
  matched_skills: string[];
  posted_at: string;
}

interface Stats {
  total_jobs: number;
  matched_count: number;
  last_synced: string | null;
}

interface JobsResponse {
  results: Job[];
  total: number;
}

const PER_PAGE = 15;

// FIX: use refs for search/page inside fetchData to avoid stale closures
export function useJobs() {
  const [matched, setMatched] = useState<Job[]>([]);
  const [allJobs, setAllJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [search, setSearch] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);
  const [tab, setTab] = useState<"matched" | "all">("matched");

  // Refs always hold the latest values — no stale closures
  const searchRef = useRef(search);
  const pageRef = useRef(page);
  useEffect(() => {
    searchRef.current = search;
  }, [search]);
  useEffect(() => {
    pageRef.current = page;
  }, [page]);

  async function fetchData(q?: string, pg?: number) {
    const query = q ?? searchRef.current;
    const pageNum = pg ?? pageRef.current;
    try {
      const params = new URLSearchParams({
        page: String(pageNum),
        per_page: String(PER_PAGE),
      });
      if (query) params.set("q", query);
      const matchedPath = query
        ? `/jobs/matched/?q=${encodeURIComponent(query)}`
        : "/jobs/matched/";

      const [matchedRes, allRes, statsRes] = await Promise.all([
        api.get<JobsResponse>(matchedPath),
        api.get<JobsResponse>(`/jobs/?${params.toString()}`),
        api.get<Stats>("/jobs/stats/"),
      ]);

      setMatched(matchedRes.data.results || []);
      setAllJobs(allRes.data.results || []);
      setTotal(allRes.data.total || 0);
      setStats(statsRes.data);
    } catch {
      // silently fail — existing state stays visible
    }
  }

  // Initial load
  useEffect(() => {
    setLoading(true);
    fetchData().finally(() => setLoading(false));
  }, []);

  // Search debounce
  const isFirstRender = useRef(true);
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    const t = setTimeout(() => {
      setPage(1);
      fetchData(search, 1);
    }, 350);
    return () => clearTimeout(t);
  }, [search]);

  // Page change
  const isFirstPage = useRef(true);
  useEffect(() => {
    if (isFirstPage.current) {
      isFirstPage.current = false;
      return;
    }
    fetchData(search, page);
  }, [page]);

  async function handleRefresh() {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }

  const totalPages = Math.ceil(total / PER_PAGE);
  const displayJobs = tab === "matched" ? matched : allJobs;

  return {
    matched,
    allJobs,
    stats,
    loading,
    refreshing,
    search,
    setSearch,
    page,
    setPage,
    total,
    totalPages,
    tab,
    setTab,
    displayJobs,
    handleRefresh,
  };
}
