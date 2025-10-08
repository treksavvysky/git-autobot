import RepositoryDashboardClient from "./RepositoryDashboardClient";
import ErrorMessage from "@/components/ErrorMessage";
import { apiClient } from "@/lib/api";

export const dynamic = "force-dynamic";

type PageProps = {
  params: { name?: string };
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default async function RepositoryDashboardPage({
  params,
  searchParams,
}: PageProps) {
  const name = params?.name ?? "";
  const tokenParam = searchParams?.token;
  const token = Array.isArray(tokenParam) ? tokenParam[0] : tokenParam;

  if (!name) {
    return (
      <div className="min-h-screen bg-gray-900 py-8">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <ErrorMessage title="Missing repository" message="Repository name is required." />
        </div>
      </div>
    );
  }

  try {
    const [
      overview,
      syncStatus,
      branches,
      commits,
      issues,
      recurringTasks,
      ciLatest,
      health,
      notes,
      snippets,
    ] = await Promise.all([
      apiClient.getRepositoryDetails(name, token),
      apiClient.getSyncStatus(name, token),
      apiClient.getBranches(name, token),
      apiClient.getCommits(name, token),
      apiClient.getIssues(name, token),
      apiClient.getRecurringTasks(name),
      apiClient.getLatestAction(name),
      apiClient.getHealth(name),
      apiClient.getNotes(name),
      apiClient.getSnippets(name),
    ]);

    const [localRepo] = await Promise.allSettled([
      apiClient.getLocalRepository(name),
    ]);

    return (
      <RepositoryDashboardClient
        name={name}
        overview={overview}
        syncStatus={syncStatus}
        localRepo={localRepo.status === "fulfilled" ? localRepo.value : null}
        branches={branches}
        commits={commits}
        issues={issues}
        recurringTasks={recurringTasks}
        ciLatest={ciLatest}
        health={health}
        notes={notes}
        snippets={snippets}
      />
    );
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Failed to load repository dashboard data.";

    return (
      <div className="min-h-screen bg-gray-900 py-8">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <ErrorMessage title="Failed to load dashboard" message={message} />
        </div>
      </div>
    );
  }
}
