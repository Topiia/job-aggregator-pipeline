import { useState, useEffect, useRef } from "react";
import type { Job, Stats } from "../types/job";
import { fetchJobs, fetchStats } from "../api/client";
import StatsPanel from "../components/StatsPanel";
import FilterBar from "../components/FilterBar";
import JobCard from "../components/JobCard";

export default function Dashboard() {
  // ── Theme State
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "theme1");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

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
          let updatedData = data;
          if (offset === 0) {
            updatedData = [...updatedData].sort(() => Math.random() - 0.5);
            setJobs(updatedData);
          } else {
            setJobs((prev) => [...prev, ...updatedData]);
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
    <div className="min-h-screen transition-colors duration-500 ease-in-out">
      <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col gap-6 relative">

        {/* Header */}
        <header className="sticky top-0 z-50 backdrop-blur-md bg-theme-surface/70 py-4 -mx-4 px-4 sm:mx-0 sm:px-6 rounded-b-xl sm:rounded-xl shadow-sm border border-theme-muted/20 flex flex-col sm:flex-row justify-between items-center gap-4 transition-all duration-300">
          <div className="flex items-center gap-3">
            <img src="/topia_job_aggregator.ico" alt="Topia Logo" className="w-8 h-8 object-contain drop-shadow-sm" />
            <div>
              <h1 className="text-xl sm:text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-theme-glow1 to-theme-glow2">
                Topia Job Aggregator
              </h1>
              <p className="text-xs sm:text-sm text-theme-muted mt-0.5 font-medium">
                Controlled Data Pipeline
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 bg-theme-surface/80 border border-theme-muted/20 p-1 rounded-full shadow-sm">
            <button 
              onClick={() => setTheme("theme1")} 
              className={`w-8 h-8 rounded-full border-2 transition-transform ${theme === 'theme1' ? 'border-theme-glow1 scale-110' : 'border-transparent hover:scale-105'}`}
              style={{ background: 'linear-gradient(135deg, #f8f6f0, #8b8072)' }}
              title="Theme 1: Chiffon & Dune"
            />
            <button 
              onClick={() => setTheme("theme2")} 
              className={`w-8 h-8 rounded-full border-2 transition-transform ${theme === 'theme2' ? 'border-theme-glow1 scale-110' : 'border-transparent hover:scale-105'}`}
              style={{ background: 'linear-gradient(135deg, #fdfafb, #d4a5b4)' }}
              title="Theme 2: Hellebore & Magnolia"
            />
            <button 
              onClick={() => setTheme("theme3")} 
              className={`w-8 h-8 rounded-full border-2 transition-transform ${theme === 'theme3' ? 'border-theme-glow1 scale-110' : 'border-transparent hover:scale-105'}`}
              style={{ background: 'linear-gradient(135deg, #f0fdf4, #34d399)' }}
              title="Theme 3: Mint & Evergreen"
            />
          </div>
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
          {!loading && !error && (
            <div className="mb-4">
              {jobs.length > 0 ? (
                <p className="text-sm text-theme-text font-medium">
                  Showing {jobs.length}{hasMore ? " results" : " results (all loaded)"}
                  {source && ` from ${source}`}
                  {` · last ${
                    days ? `${days} days` :
                    (debouncedKeyword || source) ? "90 days" : "10 days"
                  }`}
                </p>
              ) : null}
              <p className="text-xs text-theme-muted mt-0.5 font-medium">
                {stats ? `${stats.total_stored_jobs} total jobs in database` : ""}
              </p>
            </div>
          )}

          {loading && jobs.length === 0 && (
            <p className="text-center mt-10 text-theme-muted font-medium">Loading...</p>
          )}

          {error && jobs.length === 0 && (
            <p className="text-center mt-10 text-theme-glow3 font-medium">{error}</p>
          )}

          {!loading && !error && jobs.length === 0 && (
            <p className="text-center mt-10 text-theme-muted font-medium">
              {source
                ? `No recent jobs found for ${source}`
                : debouncedKeyword
                ? `No results for "${debouncedKeyword}"`
                : "No jobs found"}
            </p>
          )}

          {jobs.length > 0 && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {jobs.map((job) => (
                  <JobCard key={job.id} {...job} />
                ))}
              </div>

              {loading && (
                <p className="text-center mt-4 text-theme-muted font-medium">Loading more...</p>
              )}

              {!hasMore && (
                <p className="text-center mt-6 mb-4 text-theme-muted text-sm font-medium">No more jobs</p>
              )}

              {error && (
                <p className="text-center mt-8 mb-4 text-theme-glow3 font-medium">{error}</p>
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
