"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";

import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";
import { apiClient } from "@/lib/api";

export default function RepositoryReadmePage() {
  const params = useParams<{ name: string }>();
  const searchParams = useSearchParams();
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const repoName = params?.name ?? "";
  const token = searchParams.get("token") ?? undefined;

  const fetchReadme = useCallback(async () => {
    if (!repoName) {
      setError("Repository name is missing.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const readmeContent = await apiClient.getRepositoryReadme(repoName, token);
      setContent(readmeContent);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load README content"
      );
    } finally {
      setLoading(false);
    }
  }, [repoName, token]);

  useEffect(() => {
    fetchReadme();
  }, [fetchReadme]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {repoName ? `${repoName} README` : "Repository README"}
            </h1>
            <p className="text-gray-600">
              View the README content fetched from your GitHub repository.
            </p>
          </div>
          <Link
            href="/repositories"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
          >
            Back to Repositories
          </Link>
        </div>

        {loading && <LoadingSpinner />}

        {error && (
          <ErrorMessage
            title="Error Loading README"
            message={error}
            onRetry={fetchReadme}
          />
        )}

        {!loading && !error && (
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800">
              {content || "This repository does not have a README."}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
