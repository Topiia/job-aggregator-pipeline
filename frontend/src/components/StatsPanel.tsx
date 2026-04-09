type StatCardProps = {
  label: string;
  value: number;
};

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="p-4 rounded-xl shadow-md bg-white flex flex-col gap-1 min-w-[120px]">
      <span className="text-2xl font-bold text-gray-800">{value}</span>
      <span className="text-sm text-gray-500">{label}</span>
    </div>
  );
}

type Props = {
  totalJobs: number;
  sources: {
    remoteok: number;
    arbeitnow: number;
    hackernews: number;
  };
};

export default function StatsPanel({ totalJobs, sources }: Props) {
  return (
    <div className="flex flex-wrap gap-4">
      <StatCard label="Total Jobs" value={totalJobs} />
      <StatCard label="RemoteOK" value={sources.remoteok} />
      <StatCard label="Arbeitnow" value={sources.arbeitnow} />
      <StatCard label="HackerNews" value={sources.hackernews} />
    </div>
  );
}
