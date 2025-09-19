import { Repository } from "@/types/repository";
import { apiClient } from "@/lib/api";
import RepositoryCard from "@/components/RepositoryCard";
import ErrorMessage from "@/components/ErrorMessage";
import TokenForm from "@/components/TokenForm";

export default async function RepositoriesPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined };
}) {
  const token = typeof searchParams.token === 'string' ? searchParams.token : undefined;

  let repositories: Repository[] = [];
  let error: string | null = null;

  try {
    repositories = await apiClient.getRepositories(token);
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to fetch repositories";
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            GitHub Repositories
          </h1>
          <p className="text-gray-300">
            View and manage your GitHub repositories
          </p>
        </div>

        <TokenForm currentToken={token} />

        {error && (
          <ErrorMessage message={error} />
        )}

        {!error && repositories.length === 0 && (
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-12 text-center">
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
            <h3 className="text-lg font-medium text-white mb-2">
              No repositories found
            </h3>
            <p className="text-gray-300">
              Make sure you have a valid GitHub token and try again.
            </p>
          </div>
        )}

        {!error && repositories.length > 0 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">
                Your Repositories ({repositories.length})
              </h2>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {repositories.map((repo, index) => (
                <RepositoryCard
                  key={repo.full_name || repo.name || `repo-${index}`}
                  repository={repo}
                  token={token}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
