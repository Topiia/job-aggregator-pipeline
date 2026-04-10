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
  const [offset, setOffset] = useState(0);
  const [days, setDays] = useState<string>("");
  
  const [hasMore, setHasMore] = useState(true);

  const hasFetchedStats = useRef(false);
  const requestIdRef = useRef(0);
  const loaderRef = useRef<HTMLDivElement | null>(null);
  const isFetchingRef = useRef(false);

  // ── Debounce keyword isolated ──────────────────────────────────────────────
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedKeyword(keyword);
    }, 300);
    return () => clearTimeout(timer);
  }, [keyword]);

  // ── Reset pagination on filter change ──────────────────────────────────────
  useEffect(() => {
    setLimit(20);
    setOffset(0);
    setJobs([]);
    setHasMore(true);
    isFetchingRef.current = false;
  }, [keyword, source, days]);

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

  // ── Infinite Scroll Observer ───────────────────────────────────────────────
  useEffect(() => {
    if (!loaderRef.current) return;
    if (!hasMore) return; // double guard

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        // Prevent over-fetch boundaries and guard against overlapping requests
        if (
          entry.isIntersecting &&
          !loading &&
          !isFetchingRef.current &&
          hasMore
        ) {
          isFetchingRef.current = true;
          setOffset((prev) => prev + limit);
        }
      },
      {
        root: null,
        rootMargin: "200px",
        threshold: 0,
      }
    );

    observer.observe(loaderRef.current);

    return () => observer.disconnect();
  }, [loading, limit, hasMore]);

  // ── Fetch jobs on mount or filter change ───────────────────────────────────
  useEffect(() => {
    if (debouncedKeyword && debouncedKeyword.length < 2) return;
    if (offset > 0 && !hasMore) return; // double guard

    const currentRequestId = ++requestIdRef.current;

    setLoading(true);
    isFetchingRef.current = true;
    setError(null);
    
    fetchJobs({ source, keyword: debouncedKeyword, limit, offset, days })
      .then((data) => {
        if (currentRequestId === requestIdRef.current) {
          if (offset === 0) {
            setJobs(data);
          } else {
            setJobs((prev) => [...prev, ...data]);
          }
          
          if (offset === 0 && data.length === 0) {
            setHasMore(false);
          } else if (data.length < limit) {
            setHasMore(false);
          } else {
            setHasMore(true);
          }
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
          isFetchingRef.current = false;
        }
      });
  }, [source, debouncedKeyword, limit, offset, days]);

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
            days={days}
            onKeywordChange={setKeyword}
            onSourceChange={setSource}
            onLimitChange={setLimit}
            onDaysChange={setDays}
          />
        </section>

        {/* Job Grid */}
        <section>
          {!loading && !error && stats && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 font-medium">
                Showing {jobs.length} {hasMore ? "" : "(all)"} of {stats.total_stored_jobs} stored jobs
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {debouncedKeyword || source 
                  ? "Showing results from last 90 days" 
                  : "Showing recent jobs (last 10 days)"}
              </p>
            </div>
          )}

          {loading && jobs.length === 0 && (
            <p className="text-center mt-10 text-gray-500">Loading...</p>
          )}

          {error && jobs.length === 0 && (
            <p className="text-center mt-10 text-red-500">{error}</p>
          )}

          {!loading && !error && jobs.length === 0 && (
            <p className="text-center mt-10 text-gray-500">No jobs found</p>
          )}

          {jobs.length > 0 && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {jobs.map((job) => (
                  <JobCard key={job.id} {...job} />
                ))}
              </div>

              {loading && (
                <p className="text-center mt-4 text-gray-500">Loading more...</p>
              )}

              {!hasMore && (
                <p className="text-center mt-6 mb-4 text-gray-500 text-sm">No more jobs</p>
              )}

              {error && (
                <p className="text-center mt-8 mb-4 text-red-500">{error}</p>
              )}

              {hasMore && (
                <div ref={loaderRef} className="h-4 w-full mt-4"></div>
              )}
            </>
          )}
        </section>

      </div>
    </div>
  );
}
