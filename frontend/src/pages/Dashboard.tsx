import { useState, useEffect, useRef } from "react";
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
  const [debouncedKeyword, setDebouncedKeyword] = useState("");
  const [source, setSource] = useState("");
  const [limit, setLimit] = useState(20);

  const hasFetchedStats = useRef(false);
  const requestIdRef = useRef(0);

  // ── Debounce keyword isolated ──────────────────────────────────────────────
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedKeyword(keyword);
    }, 300);
    return () => clearTimeout(timer);
  }, [keyword]);

  // ── Reset limit on filter change ───────────────────────────────────────────
  useEffect(() => {
    setLimit(20);
  }, [keyword, source]);

  // ── Fetch stats ONCE (Strict Mode safe) ────────────────────────────────────
  useEffect(() => {
    if (hasFetchedStats.current) return;
    hasFetchedStats.current = true;

    fetchStats()
      .then(setStats)
      .catch(() => {
        // Stats failure is non-critical
        console.error("Failed to load stats");
      });
  }, []);

  // ── Fetch jobs on mount or filter change ───────────────────────────────────
  useEffect(() => {
    if (debouncedKeyword && debouncedKeyword.length < 2) return;

    const currentRequestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);
    
    fetchJobs({ source, keyword: debouncedKeyword, limit })
      .then((data) => {
        if (currentRequestId === requestIdRef.current) {
          setJobs(data);
        }
      })
      .catch(() => {
        if (currentRequestId === requestIdRef.current) {
          setError("Failed to load data");
        }
      })
      .finally(() => {
        if (currentRequestId === requestIdRef.current) {
          setLoading(false);
        }
      });
  }, [source, debouncedKeyword, limit]);

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
          {!loading && !error && stats && (
            <p className="text-sm text-gray-600 mb-4 font-medium">
              Showing {jobs.length} of {stats.total_stored_jobs} jobs
            </p>
          )}

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
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {jobs.map((job) => (
                  <JobCard key={job.id} {...job} />
                ))}
              </div>

              {stats && jobs.length < stats.total_stored_jobs && (
                <div className="flex justify-center mt-8">
                  <button
                    onClick={() => setLimit((prev) => prev + 20)}
                    className="px-6 py-2 bg-white border border-gray-300 text-gray-700 rounded-md shadow-sm hover:bg-gray-50 font-medium transition"
                  >
                    Load More
                  </button>
                </div>
              )}
            </>
          )}
        </section>

      </div>
    </div>
  );
}
