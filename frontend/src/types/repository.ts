export interface Repository {
  name: string;
  full_name?: string;
  html_url?: string;
  description?: string;
  visibility: string;
  default_branch: string;
  language?: string;
  updated_at?: string;
}

export interface ApiError {
  detail: string;
}

export interface ReadmeResponse {
  content: string;
}
