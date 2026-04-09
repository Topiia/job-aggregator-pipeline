type Props = {
  title: string;
  company: string;
  source: string;
  posted_at: string;
  url: string;
};

export default function JobCard({ title, company, source, posted_at, url }: Props) {
  return (
    <div className="p-4 rounded-xl shadow-md bg-white flex flex-col gap-2">
      <h3 className="font-semibold text-sm sm:text-base line-clamp-2">{title}</h3>
      <p className="text-gray-500 text-sm">{company}</p>
      <div className="flex items-center gap-2 mt-auto pt-2">
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full capitalize">
          {source}
        </span>
        <span className="text-xs text-gray-400 ml-auto">
          {new Date(posted_at).toLocaleString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 text-sm font-medium break-words hover:underline"
      >
        Apply →
      </a>
    </div>
  );
}
