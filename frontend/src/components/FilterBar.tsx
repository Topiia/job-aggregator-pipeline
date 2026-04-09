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
    <div className="flex flex-col sm:flex-row gap-2">
      <input
        type="text"
        placeholder="Search by keyword..."
        value={keyword}
        onChange={(e) => onKeywordChange(e.target.value)}
        className="w-full sm:w-auto border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      <select
        value={source}
        onChange={(e) => onSourceChange(e.target.value)}
        className="w-full sm:w-auto border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      >
        <option value="">All Sources</option>
        <option value="remoteok">RemoteOK</option>
        <option value="arbeitnow">Arbeitnow</option>
        <option value="hackernews">HackerNews</option>
      </select>
      <select
        value={limit}
        onChange={(e) => onLimitChange(Number(e.target.value))}
        className="w-full sm:w-auto border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      >
        <option value={10}>10 results</option>
        <option value={20}>20 results</option>
        <option value={50}>50 results</option>
      </select>
      <select
        value={days}
        onChange={(e) => onDaysChange(e.target.value)}
        className="w-full sm:w-auto border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      >
        <option value="">Default Timeline</option>
        <option value="1">Last 24 hours</option>
        <option value="7">Last 7 days</option>
        <option value="30">Last 30 days</option>
        <option value="90">Last 90 days</option>
      </select>
    </div>
  );
}
