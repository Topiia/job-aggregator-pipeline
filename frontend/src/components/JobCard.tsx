type Props = {
  title: string;
  company: string;
  source: string;
  posted_at: string;
  url: string;
};

export default function JobCard({ title, company, source, posted_at, url }: Props) {
  return (
    <div className="relative rounded-xl p-[1px] bg-gradient-to-r from-theme-glow1 via-theme-glow2 to-theme-glow3 hover:scale-[1.02] hover:shadow-lg transition-transform duration-300">
      <div className="bg-theme-surface rounded-xl p-4 flex flex-col gap-2 h-full justify-between">
        <div className="flex flex-col gap-1">
          <h3 className="font-bold text-sm sm:text-base line-clamp-2 text-theme-text">{title}</h3>
          <p className="font-medium text-theme-muted text-sm">{company}</p>
        </div>
        
        <div className="flex items-center gap-2 mt-4 pt-2 border-t border-theme-muted/20">
          <span className="text-xs bg-theme-bg text-theme-text px-2 py-0.5 rounded-full capitalize font-medium">
            {source}
          </span>
          <span className="text-xs text-theme-muted ml-auto">
            {new Date(posted_at).toLocaleString("en-IN", {
              day: "2-digit",
              month: "short",
              year: "numeric",
            })}
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
