type Props = {
  keyword: string;
  source: string;
  limit: number;
  days: string;
  onKeywordChange: (value: string) => void;
  onSourceChange: (value: string) => void;
  onLimitChange: (value: number) => void;
  onDaysChange: (value: string) => void;
};

export default function FilterBar({
  keyword,
  source,
  limit,
  days,
  onKeywordChange,
  onSourceChange,
  onLimitChange,
  onDaysChange,
}: Props) {
  return (
    <div className="flex flex-col md:flex-row gap-3 bg-theme-surface/50 p-4 rounded-xl shadow-sm border border-theme-muted/10 backdrop-blur-sm">
      <div className="flex-1">
        <input
          type="text"
          placeholder="Search roles, companies..."
          value={keyword}
          onChange={(e) => onKeywordChange(e.target.value)}
          className="w-full border border-theme-muted/20 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-theme-glow1 bg-white/50 text-theme-text placeholder-theme-muted/60 transition-all font-medium"
        />
      </div>
      <div className="flex flex-col sm:flex-row gap-3">
        <select
          value={source}
          onChange={(e) => onSourceChange(e.target.value)}
          className="w-full sm:w-auto min-w-[140px] border border-theme-muted/20 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-theme-glow1 bg-white/50 text-theme-text transition-all cursor-pointer font-medium"
        >
          <option value="">All Sources</option>
          <option value="remoteok">RemoteOK</option>
          <option value="arbeitnow">Arbeitnow</option>
          <option value="hackernews">HackerNews</option>
        </select>
        <select
          value={limit}
          onChange={(e) => onLimitChange(Number(e.target.value))}
          className="w-full sm:w-auto border border-theme-muted/20 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-theme-glow1 bg-white/50 text-theme-text transition-all cursor-pointer font-medium"
        >
          <option value={10}>10 per page</option>
          <option value={20}>20 per page</option>
          <option value={50}>50 per page</option>
        </select>
        <select
          value={days}
          onChange={(e) => onDaysChange(e.target.value)}
          className="w-full sm:w-auto border border-theme-muted/20 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-theme-glow1 bg-white/50 text-theme-text transition-all cursor-pointer font-medium"
        >
          <option value="">Default Timeline</option>
          <option value="1">Last 24 hours</option>
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>
    </div>
  );
}
