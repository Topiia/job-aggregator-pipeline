type StatCardProps = {
  label: string;
  value: number;
};

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="p-4 rounded-xl shadow-sm bg-theme-surface/50 border border-theme-muted/10 backdrop-blur-sm flex flex-col gap-1 min-w-[120px] flex-1">
      <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-theme-glow1 to-theme-glow2">{value}</span>
      <span className="text-sm text-theme-muted font-medium">{label}</span>
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
    <div className="flex flex-wrap gap-4 w-full">
      <StatCard label="Total Jobs" value={totalJobs} />
      <StatCard label="RemoteOK" value={sources.remoteok} />
      <StatCard label="Arbeitnow" value={sources.arbeitnow} />
      <StatCard label="HackerNews" value={sources.hackernews} />
    </div>
  );
}
