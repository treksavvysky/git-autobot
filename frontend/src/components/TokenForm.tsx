"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface TokenFormProps {
  currentToken?: string;
}

export default function TokenForm({ currentToken }: TokenFormProps) {
  const [githubToken, setGithubToken] = useState(currentToken || "");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    const trimmed = githubToken.trim();
    if (trimmed) params.set('token', trimmed);
    router.push(`?${params.toString()}`);
  };

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-lg font-semibold text-white mb-4">
        GitHub Authentication
      </h2>
      <form onSubmit={handleSubmit} className="flex gap-4">
        <div className="flex-1">
          <label
            htmlFor="github-token"
            className="block text-sm font-medium text-gray-300 mb-2"
          >
            GitHub Personal Access Token
          </label>
          <input
            type="password"
            id="github-token"
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            placeholder="Enter your GitHub token (optional)"
            className="w-full px-3 py-2 border border-gray-600 bg-gray-700 text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 placeholder-gray-400"
          />
          <p className="mt-1 text-sm text-gray-400">
            Leave empty to use environment variable or provide your token
            for authentication
          </p>
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            className="px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            Load Repositories
          </button>
        </div>
      </form>
    </div>
  );
}