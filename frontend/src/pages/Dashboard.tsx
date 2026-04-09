import { useState, useEffect, useCallback } from "react";
import type { Job, Stats } from "../types/job";
import { fetchJobs, fetchStats } from "../api/client";
import StatsPanel from "../components/StatsPanel";
import FilterBar from "../components/FilterBar";
import JobCard from "../components/JobCard";

export default function Dashboard() {
  // ── State ──────────────────────────────────────────────────────────────────
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [keyword, setKeyword] = useState("");
  const [source, setSource] = useState("");
  const [limit, setLimit] = useState(20);

  // ── Fetch stats once on mount ──────────────────────────────────────────────
  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(() => {
        // Stats failure is non-critical — don't block the whole page
        console.error("Failed to load stats");
      });
  }, []);

  // ── Fetch jobs (re-runs when source or limit changes immediately) ──────────
  const loadJobs = useCallback(
    (kw: string, src: string, lim: number) => {
      setLoading(true);
      setError(null);
      fetchJobs({ keyword: kw || undefined, source: src || undefined, limit: lim })
        .then((data) => {
          setJobs(data);
          setLoading(false);
        })
        .catch(() => {
          setError("Failed to load data");
          setLoading(false);
        });
    },
    []
  );

  // Initial load
  useEffect(() => {
    loadJobs(keyword, source, limit);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-fetch when source or limit changes (no debounce needed)
  useEffect(() => {
    loadJobs(keyword, source, limit);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, limit]);

  // Re-fetch keyword with 300ms debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      loadJobs(keyword, source, limit);
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keyword]);

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col gap-6">

        {/* Header */}
        <header>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Job Aggregator
          </h1>
          <p className="text-sm sm:text-base text-gray-500 mt-1">
            Controlled Data Pipeline
          </p>
        </header>

        {/* Stats */}
        {stats && (
          <section>
            <StatsPanel
              totalJobs={stats.total_stored_jobs}
              sources={stats.sources}
            />
          </section>
        )}

        {/* Filters */}
        <section>
          <FilterBar
            keyword={keyword}
            source={source}
            limit={limit}
            onKeywordChange={setKeyword}
            onSourceChange={setSource}
            onLimitChange={setLimit}
          />
        </section>

        {/* Job Grid */}
        <section>
          {loading && (
            <p className="text-center mt-10 text-gray-500">Loading...</p>
          )}

          {!loading && error && (
            <p className="text-center mt-10 text-red-500">{error}</p>
          )}

          {!loading && !error && jobs.length === 0 && (
            <p className="text-center mt-10 text-gray-500">No jobs found</p>
          )}

          {!loading && !error && jobs.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {jobs.map((job) => (
                <JobCard key={job.id} {...job} />
              ))}
            </div>
          )}
        </section>

      </div>
    </div>
  );
}
