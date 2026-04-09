type Props = {
  keyword: string;
  source: string;
  limit: number;
  onKeywordChange: (value: string) => void;
  onSourceChange: (value: string) => void;
  onLimitChange: (value: number) => void;
};

export default function FilterBar({
  keyword,
  source,
  limit,
  onKeywordChange,
  onSourceChange,
  onLimitChange,
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
    </div>
  );
}
