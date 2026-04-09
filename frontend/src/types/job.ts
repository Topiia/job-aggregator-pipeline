export type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  url: string;
  source: string;
  posted_at: string;
};

export type Stats = {
  total_stored_jobs: number;
  sources: {
    remoteok: number;
    arbeitnow: number;
    hackernews: number;
  };
};

export type JobsResponse = {
  count: number;
  results: Job[];
};
