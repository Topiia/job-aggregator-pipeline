type Props = {
  title: string;
  company: string;
  location: string;
  source: string;
  posted_at: string;
  url: string;
};

function formatRelative(dateStr: string): string {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return "Unknown date";

  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return `${Math.floor(days / 7)}w ago`;
}

function formatFull(dateStr: string): string {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return "";
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function JobCard({ title, company, location, source, posted_at, url }: Props) {
  const relative = formatRelative(posted_at);
  const full = formatFull(posted_at);

  return (
    <div className="relative rounded-xl p-[1px] bg-gradient-to-r from-theme-glow1 via-theme-glow2 to-theme-glow3 hover:scale-[1.02] hover:shadow-lg transition-transform duration-300">
      <div className="bg-theme-surface rounded-xl p-4 flex flex-col gap-2 h-full justify-between">

        {/* Top: Date badge pinned top-right */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-bold text-sm sm:text-base line-clamp-2 text-theme-text flex-1">{title}</h3>
          <span
            className="text-xs text-theme-muted shrink-0 whitespace-nowrap"
            title={full}
          >
            🕒 {relative}
          </span>
        </div>

        {/* Company + Location */}
        <div className="flex flex-col gap-0.5">
          <p className="font-medium text-theme-muted text-sm truncate">{company}</p>
          {location && (
            <p className="text-xs text-theme-muted/70 truncate">{location}</p>
          )}
        </div>

        {/* Footer: source + full date */}
        <div className="flex items-center gap-2 mt-3 pt-2 border-t border-theme-muted/20">
          <span className="text-xs bg-theme-bg text-theme-text px-2 py-0.5 rounded-full capitalize font-medium shrink-0">
            {source}
          </span>
          <span className="text-xs text-theme-muted ml-auto truncate text-right" title={full}>
            📅 {full}
          </span>
        </div>

        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="absolute inset-0 z-10"
          aria-label={`Apply for ${title} at ${company}`}
        ></a>
      </div>
    </div>
  );
}
