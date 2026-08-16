export type IndexStatus =
  | "pending"
  | "cloning"
  | "scanning"
  | "indexing"
  | "ready"
  | "failed";

export interface Repository {
  id: string;
  github_url: string;
  owner: string;
  name: string;
  default_branch: string;
  languages: Record<string, number>;
  file_count: number;
  line_count: number;
  chunk_count: number;
  index_status: IndexStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  last_analyzed_at: string | null;
}

export interface RepositoryFile {
  file_path: string;
  language: string | null;
  line_count: number;
  size_bytes: number;
  indexed: boolean;
}

export interface SourceCitation {
  file_path: string;
  start_line: number;
  end_line: number;
  symbol: string | null;
  snippet: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceCitation[];
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: SourceCitation[];
  grounded: boolean;
}

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Category =
  | "bug"
  | "security"
  | "performance"
  | "maintainability"
  | "best_practice";

export interface ReviewIssue {
  severity: Severity;
  category: Category;
  file: string | null;
  line: number | null;
  title: string;
  description: string;
  recommendation: string;
}

export interface ReviewResponse {
  id: string;
  summary: string;
  issues: ReviewIssue[];
}
