import { ApiError, Repository, ReadmeResponse } from "@/types/repository";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = "Request failed";
    try {
      const errorBody = (await response.json()) as Partial<ApiError>;
      if (errorBody.detail) {
        errorMessage = errorBody.detail;
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
    const url = new URL(`${API_BASE_URL}/repos/${encodeURIComponent(name)}/readme`);
    if (token) {
      url.searchParams.set("token", token);
    }

    const response = await fetch(url.toString(), {
      cache: "no-store",
    });

    const data = await handleResponse<ReadmeResponse>(response);
    return data.content;
  }
}

export const apiClient = new ApiClient();
