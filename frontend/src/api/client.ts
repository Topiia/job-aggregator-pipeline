import type { Job, JobsResponse, Stats } from "../types/job";

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type FetchJobsParams = {
  source?: string;
  keyword?: string;
  limit?: number;
  offset?: number;
  days?: string;
};

export async function fetchJobs(params: FetchJobsParams = {}): Promise<Job[]> {
  const query = new URLSearchParams();

  if (params.source) {
    query.append("source", params.source);
  }
  if (params.keyword) {
    query.append("keyword", params.keyword);
  }
  if (params.limit !== undefined) {
    query.append("limit", params.limit.toString());
  }
  if (params.offset !== undefined) {
    query.append("offset", params.offset.toString());
  }
  if (params.days) {
    query.append("days", params.days);
  }

  const queryString = query.toString();
  const url = queryString ? `${BASE_URL}/jobs?${queryString}` : `${BASE_URL}/jobs`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  let response: Response;
  try {
    response = await fetch(url, { signal: controller.signal });
  } catch (err) {
    if ((err as Error).name === "AbortError") {
      throw new Error("Request timeout");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch jobs: ${response.statusText}`);
  }

  const data: JobsResponse = await response.json();
  return data.results;
}

export async function fetchStats(): Promise<Stats> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/stats`, { signal: controller.signal });
  } catch (err) {
    if ((err as Error).name === "AbortError") {
      throw new Error("Request timeout");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }

  const data: Stats = await response.json();
  return data;
}
