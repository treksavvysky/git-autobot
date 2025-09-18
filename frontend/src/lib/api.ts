import { ApiError, Repository, ReadmeResponse } from "@/types/repository";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = "Request failed";
    try {
      const errorBody = (await response.json()) as any;
      if (typeof errorBody?.error?.message === "string") {
        errorMessage = errorBody.error.message as string;
      } else if (typeof errorBody?.detail === "string") {
        errorMessage = errorBody.detail as string;
      } else if (typeof errorBody?.detail?.error?.message === "string") {
        errorMessage = errorBody.detail.error.message as string;
      } else if (typeof errorBody === "string") {
        errorMessage = errorBody;
      } else if (errorBody) {
        errorMessage = JSON.stringify(errorBody);
      }
    } catch {
      // Ignore JSON parsing errors and use default message
    }
    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}

class ApiClient {
  async getRepositories(token?: string): Promise<Repository[]> {
    const url = new URL(`${API_BASE_URL}/repos`);
    if (token) {
      url.searchParams.set("token", token);
    }

    const response = await fetch(url.toString(), {
      cache: "no-store",
    });

    return handleResponse<Repository[]>(response);
  }

  async getRepositoryReadme(name: string, token?: string): Promise<string> {
    const url = new URL(
      `${API_BASE_URL}/repos/${encodeURIComponent(name)}/readme`
    );
    if (token) {
      url.searchParams.set("token", token);
    }

    const response = await fetch(url.toString(), {
      cache: "no-store",
    });

    const data = await handleResponse<ReadmeResponse>(response);
    return data.content;
  }

  async getRepositoryDetails(name: string, token?: string): Promise<any> {
    const url = new URL(`${API_BASE_URL}/repos/${encodeURIComponent(name)}`);
    if (token) url.searchParams.set("token", token);
    const resp = await fetch(url.toString(), { cache: "no-store" });
    return handleResponse<any>(resp);
  }

  async getSyncStatus(name: string, token?: string): Promise<any> {
    const url = new URL(
      `${API_BASE_URL}/repos/${encodeURIComponent(name)}/sync-status`
    );
    if (token) url.searchParams.set("token", token);
    const resp = await fetch(url.toString(), { cache: "no-store" });
    return handleResponse<any>(resp);
  }

  async getBranches(name: string, token?: string): Promise<any[]> {
    const url = new URL(
      `${API_BASE_URL}/repos/${encodeURIComponent(name)}/branches`
    );
    if (token) url.searchParams.set("token", token);
    const resp = await fetch(url.toString(), { cache: "no-store" });
    return handleResponse<any[]>(resp);
  }

  async getCommits(name: string, token?: string): Promise<any[]> {
    const url = new URL(
      `${API_BASE_URL}/repos/${encodeURIComponent(name)}/commits`
    );
    if (token) url.searchParams.set("token", token);
    const resp = await fetch(url.toString(), { cache: "no-store" });
    return handleResponse<any[]>(resp);
  }

  async getIssues(name: string, token?: string): Promise<any[]> {
    const url = new URL(
      `${API_BASE_URL}/repos/${encodeURIComponent(name)}/issues`
    );
    if (token) url.searchParams.set("token", token);
    const resp = await fetch(url.toString(), { cache: "no-store" });
    return handleResponse<any[]>(resp);
  }

  async getRecurringTasks(name: string): Promise<any[]> {
    const url = new URL(
      `${API_BASE_URL}/repos/${encodeURIComponent(name)}/tasks/recurring`
    );
    const resp = await fetch(url.toString(), { cache: "no-store" });
    return handleResponse<any[]>(resp);
  }

  async toggleRecurringTask(name: string, id: string): Promise<any> {
    const url = `${API_BASE_URL}/repos/${encodeURIComponent(
      name
    )}/tasks/recurring/${encodeURIComponent(id)}/toggle`;
    const resp = await fetch(url, { method: "POST" });
    return handleResponse<any>(resp);
  }

  async getLatestAction(name: string): Promise<any> {
    const url = `${API_BASE_URL}/repos/${encodeURIComponent(
      name
    )}/ci/actions/latest`;
    const resp = await fetch(url, { cache: "no-store" });
    return handleResponse<any>(resp);
  }

  async getHealth(name: string): Promise<any> {
    const url = `${API_BASE_URL}/repos/${encodeURIComponent(name)}/health`;
    const resp = await fetch(url, { cache: "no-store" });
    return handleResponse<any>(resp);
  }

  async getNotes(name: string): Promise<any[]> {
    const url = `${API_BASE_URL}/repos/${encodeURIComponent(name)}/notes/`;
    const resp = await fetch(url, { cache: "no-store" });
    return handleResponse<any[]>(resp);
  }

  async createNote(name: string, body: { content: string }): Promise<any> {
    const url = `${API_BASE_URL}/repos/${encodeURIComponent(name)}/notes/`;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse<any>(resp);
  }

  async getSnippets(name: string): Promise<any[]> {
    const url = `${API_BASE_URL}/repos/${encodeURIComponent(name)}/snippets/`;
    const resp = await fetch(url, { cache: "no-store" });
    return handleResponse<any[]>(resp);
  }

  async createSnippet(
    name: string,
    body: { title: string; content: string; language?: string }
  ): Promise<any> {
    const url = `${API_BASE_URL}/repos/${encodeURIComponent(name)}/snippets/`;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse<any>(resp);
  }

  // Local repo endpoints
  async getLocalRepository(name: string): Promise<any> {
    const url = `${API_BASE_URL}/local/repos/${encodeURIComponent(name)}`;
    const resp = await fetch(url, { cache: "no-store" });
    return handleResponse<any>(resp);
  }

  async getLocalLog(name: string, limit = 50): Promise<any> {
    const url = new URL(
      `${API_BASE_URL}/local/repos/${encodeURIComponent(name)}/log`
    );
    url.searchParams.set("limit", String(limit));
    const resp = await fetch(url.toString(), { cache: "no-store" });
    return handleResponse<any>(resp);
  }

  async getLocalDiff(
    name: string,
    target = "HEAD",
    mode: "summary" | "patch" = "summary"
  ): Promise<any> {
    const url = new URL(
      `${API_BASE_URL}/local/repos/${encodeURIComponent(name)}/diff`
    );
    url.searchParams.set("target", target);
    url.searchParams.set("mode", mode);
    const resp = await fetch(url.toString(), { cache: "no-store" });
    return handleResponse<any>(resp);
  }

  async cloneRepository(name: string, remote_url?: string): Promise<any> {
    const url = `${API_BASE_URL}/local/repos/${encodeURIComponent(name)}/clone`;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ remote_url }),
    });
    return handleResponse<any>(resp);
  }

  async pullRepository(name: string, body: { rebase: boolean }): Promise<any> {
    const url = `${API_BASE_URL}/local/repos/${encodeURIComponent(name)}/pull`;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse<any>(resp);
  }

  async pushRepository(name: string, body: { branch?: string }): Promise<any> {
    const url = `${API_BASE_URL}/local/repos/${encodeURIComponent(name)}/push`;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse<any>(resp);
  }
}

export const apiClient = new ApiClient();
