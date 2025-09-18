"use client";

import { useState, useEffect } from "react";
import { Repository } from "@/types/repository";
import { apiClient } from "@/lib/api";
import RepositoryCard from "@/components/RepositoryCard";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [githubToken, setGithubToken] = useState("");

  const fetchRepositories = async (token?: string) => {
    try {
      setLoading(true);
      setError(null);
      const repos = await apiClient.getRepositories(token);
      setRepositories(repos);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch repositories"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepositories();
  }, []);

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (githubToken.trim()) {
      fetchRepositories(githubToken.trim());
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            GitHub Repositories
          </h1>
          <p className="text-gray-600">
            View and manage your GitHub repositories
          </p>
        </div>

        {/* GitHub Token Input */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            GitHub Authentication
          </h2>
          <form onSubmit={handleTokenSubmit} className="flex gap-4">
            <div className="flex-1">
              <label
                htmlFor="github-token"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                GitHub Personal Access Token
              </label>
              <input
                type="password"
                id="github-token"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="Enter your GitHub token (optional)"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Leave empty to use environment variable or provide your token
                for authentication
              </p>
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {loading ? "Loading..." : "Load Repositories"}
              </button>
            </div>
          </form>
        </div>

        {/* Content */}
        {loading && <LoadingSpinner />}

        {error && (
          <ErrorMessage
            message={error}
            onRetry={() => fetchRepositories(githubToken || undefined)}
          />
        )}

        {!loading && !error && repositories.length === 0 && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <svg
              className="w-16 h-16 text-gray-400 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No repositories found
            </h3>
            <p className="text-gray-600">
              Make sure you have a valid GitHub token and try again.
            </p>
          </div>
        )}

        {!loading && !error && repositories.length > 0 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                Your Repositories ({repositories.length})
              </h2>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {repositories.map((repo) => (
                <RepositoryCard key={repo.full_name} repository={repo} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
