"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";
import { apiClient } from "@/lib/api";

export default function RepositoryDashboardPage() {
  const params = useParams<{ name: string }>();
  const searchParams = useSearchParams();
  const name = params?.name ?? "";
  const token = searchParams.get("token") ?? undefined;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<any>(null);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [localRepo, setLocalRepo] = useState<any | null>(null);
  const [branches, setBranches] = useState<any[]>([]);
  const [commits, setCommits] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);
  const [recurringTasks, setRecurringTasks] = useState<any[]>([]);
  const [ciLatest, setCiLatest] = useState<any | null>(null);
  const [health, setHealth] = useState<any | null>(null);
  const [notes, setNotes] = useState<any[]>([]);
  const [snippets, setSnippets] = useState<any[]>([]);
  const [gitLog, setGitLog] = useState<any | null>(null);
  const [diffSummary, setDiffSummary] = useState<any | null>(null);

  const loadAll = useCallback(async () => {
    if (!name) return;
    setLoading(true);
    setError(null);
    try {
      // Fetch primary GitHub-backed data (required for the page)
      const [details, sync, br, cm, is, tasks, latest, hlth, nts, snps] =
        await Promise.all([
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
      setOverview(details);
      setSyncStatus(sync);
      setBranches(br);
      setCommits(cm);
      setIssues(is);
      setRecurringTasks(tasks);
      setCiLatest(latest);
      setHealth(hlth);
      setNotes(nts);
      setSnippets(snps);
    } catch (err) {
      // If GitHub data fails, show the error (these are primary)
      setError(
        err instanceof Error ? err.message : "Failed to load dashboard data"
      );
    }

    // Fetch local repo data as optional (should not block the page)
    const [localRes, logRes, diffRes] = await Promise.allSettled([
      apiClient.getLocalRepository(name),
      apiClient.getLocalLog(name),
      apiClient.getLocalDiff(name),
    ]);

    if (localRes.status === "fulfilled") {
      setLocalRepo(localRes.value);
    } else {
      setLocalRepo(null);
    }
    if (logRes.status === "fulfilled") {
      setGitLog(logRes.value);
    } else {
      setGitLog(null);
    }
    if (diffRes.status === "fulfilled") {
      setDiffSummary(diffRes.value);
    } else {
      setDiffSummary(null);
    }

    setLoading(false);
  }, [name, token]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const localState = useMemo(() => {
    if (!localRepo) return { state: "not_found" } as const;
    const ahead = syncStatus?.ahead ?? 0;
    const behind = syncStatus?.behind ?? 0;
    if (ahead === 0 && behind === 0) return { state: "synced" } as const;
    return { state: "out_of_sync", ahead, behind } as const;
  }, [localRepo, syncStatus]);

  const doClone = async () => {
    if (!name) return;
    const remoteUrl = overview?.html_url ?? undefined;
    await apiClient.cloneRepository(name, remoteUrl);
    await loadAll();
  };

  const doPull = async (rebase: boolean) => {
    await apiClient.pullRepository(name, { rebase });
    await loadAll();
  };

  const doPush = async () => {
    await apiClient.pushRepository(name, {});
    await loadAll();
  };

  const toggleTask = async (taskId: string) => {
    await apiClient.toggleRecurringTask(name, taskId);
    await loadAll();
  };

  const addNote = async (content: string) => {
    if (!content.trim()) return;
    await apiClient.createNote(name, { content });
    await loadAll();
  };

  const addSnippet = async (title: string, content: string) => {
    if (!title.trim() || !content.trim()) return;
    await apiClient.createSnippet(name, { title, content });
    await loadAll();
  };

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{name}</h1>
            <p className="text-gray-300">Repository dashboard</p>
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
          <ErrorMessage title="Error" message={error} onRetry={loadAll} />
        )}

        {!loading && !error && (
          <div className="space-y-6">
            {/* Overview Header */}
            <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-white mb-1">
                    {overview?.name || name}
                  </h2>
                  <p className="text-gray-300">
                    {overview?.description || "No description."}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={doPush}
                    className="px-3 py-2 text-sm rounded-md bg-green-600 text-white hover:bg-green-700 border border-green-700"
                  >
                    Push Changes
                  </button>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Local State Panel */}
                <div className="md:col-span-2">
                  {localState.state === "not_found" && (
                    <div className="flex items-center justify-between bg-gray-800 border border-gray-700 rounded-md p-4">
                      <div>
                        <p className="text-white font-medium">
                          Local Status: Not Found
                        </p>
                        <p className="text-gray-400 text-sm">
                          Clone to manage locally.
                        </p>
                      </div>
                      <button
                        onClick={doClone}
                        className="px-3 py-2 text-sm rounded-md bg-green-600 text-white hover:bg-green-700 border border-green-700"
                      >
                        Clone Repository
                      </button>
                    </div>
                  )}
                  {localState.state === "synced" && (
                    <div className="flex items-center justify-between bg-gray-800 border border-gray-700 rounded-md p-4">
                      <div>
                        <p className="text-white font-medium">
                          Local Status: Synced
                        </p>
                        <p className="text-gray-400 text-sm">
                          Branch{" "}
                          {localRepo?.active_branch || overview?.default_branch}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => doPull(false)}
                          className="px-3 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 border border-blue-700"
                        >
                          Pull
                        </button>
                        <button
                          onClick={() => doPull(true)}
                          className="px-3 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 border border-blue-700"
                        >
                          Pull --rebase
                        </button>
                      </div>
                    </div>
                  )}
                  {localState.state === "out_of_sync" && (
                    <div className="flex items-center justify-between bg-gray-800 border border-gray-700 rounded-md p-4">
                      <div>
                        <p className="text-white font-medium">
                          Local Status: Out of Sync
                        </p>
                        <p className="text-gray-400 text-sm">
                          Ahead {localState.ahead} • Behind {localState.behind}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => doPull(false)}
                          className="px-3 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 border border-blue-700"
                        >
                          Pull
                        </button>
                        <button
                          onClick={() => doPull(true)}
                          className="px-3 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 border border-blue-700"
                        >
                          Pull --rebase
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                <div className="bg-gray-800 border border-gray-700 rounded-md p-4">
                  <p className="text-white font-medium mb-2">Last Commit</p>
                  <p className="text-gray-300 text-sm">
                    {overview?.last_commit?.message ||
                      localRepo?.last_commit?.message ||
                      "—"}
                  </p>
                </div>
              </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {/* Git Commands Helper */}
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-6 lg:col-span-1">
                <p className="text-white font-semibold mb-3">
                  Git Commands Helper
                </p>
                <div className="bg-gray-900 border border-gray-700 rounded-md p-3 mb-3">
                  <p className="text-gray-300 text-sm">
                    Suggested: git pull --rebase
                  </p>
                </div>
                <details className="bg-gray-900 border border-gray-700 rounded-md p-3">
                  <summary className="text-white cursor-pointer">
                    Common Commands
                  </summary>
                  <div className="mt-3 space-y-2">
                    <code className="block text-sm text-gray-300">
                      git pull --rebase
                    </code>
                    <code className="block text-sm text-gray-300">
                      git push
                    </code>
                    <code className="block text-sm text-gray-300">
                      git stash
                    </code>
                  </div>
                </details>
              </div>

              {/* Task / Workflow Panel */}
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-6 lg:col-span-1">
                <p className="text-white font-semibold mb-3">PRs & Issues</p>
                <div className="space-y-2">
                  {issues.slice(0, 5).map((it) => (
                    <div
                      key={it.id}
                      className="flex items-center justify-between"
                    >
                      <span className="text-gray-200 text-sm truncate">
                        {it.title}
                      </span>
                      <span className="text-xs text-yellow-400">
                        {it.state}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <p className="text-white font-semibold mb-2">Recurring</p>
                  <div className="space-y-2">
                    {recurringTasks.map((t) => (
                      <label
                        key={t.id}
                        className="flex items-center gap-2 text-sm text-gray-200"
                      >
                        <input
                          type="checkbox"
                          checked={t.enabled}
                          onChange={() => toggleTask(t.id)}
                          className="accent-blue-600"
                        />
                        {t.name}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Commit & Diff Tools */}
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-6 lg:col-span-1">
                <p className="text-white font-semibold mb-3">Recent Commits</p>
                <div className="max-h-56 overflow-y-auto space-y-2">
                  {commits.slice(0, 10).map((c) => (
                    <div key={c.sha} className="text-sm">
                      <p className="text-gray-200 truncate">{c.message}</p>
                      <p className="text-gray-400">
                        {c.author} • {new Date(c.date || "").toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <button className="px-3 py-2 text-sm rounded-md bg-gray-700 text-white border border-gray-600">
                    Quick-diff vs main
                  </button>
                  <button className="px-3 py-2 text-sm rounded-md bg-gray-700 text-white border border-gray-600">
                    View Staged
                  </button>
                </div>
              </div>

              {/* Branch & PR Management */}
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-6 lg:col-span-1 xl:col-span-1">
                <p className="text-white font-semibold mb-3">Branches</p>
                <div className="text-gray-300 text-sm mb-4">
                  {branches.map((b: any) => b.name).join(", ")}
                </div>
                <div className="h-24 bg-gray-900 border border-gray-700 rounded-md" />
                <div className="mt-4 flex gap-2">
                  <button className="px-3 py-2 text-sm rounded-md bg-gray-700 text-white border border-gray-600">
                    New Branch from main
                  </button>
                  <button className="px-3 py-2 text-sm rounded-md bg-gray-700 text-white border border-gray-600">
                    Delete Stale Branches
                  </button>
                </div>
              </div>

              {/* CI/CD & Health */}
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-6 lg:col-span-1 xl:col-span-1">
                <p className="text-white font-semibold mb-3">CI/CD & Health</p>
                <div className="text-sm space-y-1">
                  <p className="text-gray-300">
                    Latest Action:{" "}
                    <span className="text-gray-200">
                      {ciLatest?.name || "—"}
                    </span>
                  </p>
                  <p className="text-gray-300">
                    Health:{" "}
                    <span className="text-gray-200">
                      {health?.status || "—"}
                    </span>
                  </p>
                </div>
              </div>

              {/* Notes & Snippets */}
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-6 lg:col-span-2 xl:col-span-2">
                <p className="text-white font-semibold mb-3">Captain's Log</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <textarea
                      placeholder="New note..."
                      className="w-full bg-gray-900 border border-gray-700 rounded-md p-2 text-gray-200 mb-2"
                      rows={4}
                      onKeyDown={async (e) => {
                        const target = e.target as HTMLTextAreaElement;
                        if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                          await addNote(target.value);
                          target.value = "";
                        }
                      }}
                    />
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {notes.map((n: any) => (
                        <div
                          key={n.id}
                          className="bg-gray-900 border border-gray-700 rounded-md p-2 text-sm text-gray-200"
                        >
                          {n.content}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <input
                      type="text"
                      placeholder="Snippet title"
                      className="w-full bg-gray-900 border border-gray-700 rounded-md p-2 text-gray-200 mb-2"
                      id="snippet-title"
                    />
                    <textarea
                      placeholder="Snippet content..."
                      className="w-full bg-gray-900 border border-gray-700 rounded-md p-2 text-gray-200 mb-2"
                      rows={4}
                      id="snippet-content"
                    />
                    <button
                      className="px-3 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 border border-blue-700"
                      onClick={async () => {
                        const titleEl = document.getElementById(
                          "snippet-title"
                        ) as HTMLInputElement | null;
                        const contentEl = document.getElementById(
                          "snippet-content"
                        ) as HTMLTextAreaElement | null;
                        const title = titleEl?.value || "";
                        const content = contentEl?.value || "";
                        await addSnippet(title, content);
                        if (titleEl) titleEl.value = "";
                        if (contentEl) contentEl.value = "";
                      }}
                    >
                      Save Snippet
                    </button>
                    <div className="space-y-2 mt-3 max-h-32 overflow-y-auto">
                      {snippets.map((s: any) => (
                        <div
                          key={s.id}
                          className="bg-gray-900 border border-gray-700 rounded-md p-2 text-sm text-gray-200"
                        >
                          <p className="font-medium">{s.title}</p>
                          <pre className="whitespace-pre-wrap text-gray-300 text-xs">
                            {s.content}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Hooks */}
              <div className="bg-gray-800/50 border-2 border-blue-700 rounded-lg shadow-md p-6 lg:col-span-2 xl:col-span-2">
                <p className="text-white font-semibold mb-3">AI Assistant</p>
                <div className="flex gap-2 mb-3">
                  <button className="px-3 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 border border-blue-700">
                    Explain recent error
                  </button>
                  <button className="px-3 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 border border-blue-700">
                    Suggest next step
                  </button>
                </div>
                <div className="bg-gray-900 border border-gray-700 rounded-md p-3">
                  <p className="text-gray-300 text-sm">
                    Daily Brief will appear here.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
