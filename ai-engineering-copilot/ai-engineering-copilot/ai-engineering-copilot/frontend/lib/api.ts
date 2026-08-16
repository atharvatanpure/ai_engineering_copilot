import type {
  ChatResponse,
  Repository,
  RepositoryFile,
  ReviewResponse,
} from "@/types";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listRepositories: () => request<Repository[]>("/api/repositories"),

  getRepository: (id: string) => request<Repository>(`/api/repositories/${id}`),

  createRepository: (githubUrl: string) =>
    request<Repository>("/api/repositories", {
      method: "POST",
      body: JSON.stringify({ github_url: githubUrl }),
    }),

  indexRepository: (id: string) =>
    request<Repository>(`/api/repositories/${id}/index`, { method: "POST" }),

  listFiles: (id: string) =>
    request<RepositoryFile[]>(`/api/repositories/${id}/files`),

  getFileContent: (id: string, filePath: string) =>
    request<{ file_path: string; content: string }>(
      `/api/repositories/${id}/files/${encodeURIComponent(filePath)}`
    ),

  chat: (id: string, question: string, sessionId?: string) =>
    request<ChatResponse>(`/api/repositories/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ question, session_id: sessionId }),
    }),

  review: (payload: {
    repository_id?: string;
    file_path?: string;
    diff?: string;
    code?: string;
  }) =>
    request<ReviewResponse>("/api/review", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export { ApiError };
