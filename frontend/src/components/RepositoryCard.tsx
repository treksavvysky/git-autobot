"use client";
import { Repository } from "@/types/repository";
import { useEffect, useRef } from "react";

interface RepositoryCardProps {
  repository: Repository;
  token?: string;
}

export default function RepositoryCard({
  repository,
  token,
}: RepositoryCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);

  const dashboardHref = token
    ? `/repositories/${encodeURIComponent(
        repository.name
      )}?token=${encodeURIComponent(token)}`
    : `/repositories/${encodeURIComponent(repository.name)}`;

  const formatLastUpdated = (dateString?: string) => {
    if (!dateString) return "Unknown";
    return new Date(dateString).toLocaleDateString();
  };

  useEffect(() => {
    // Trigger the card enter animation
    const timer = setTimeout(() => {
      if (cardRef.current) {
        cardRef.current.classList.add("card-enter-active");
      }
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  const handleClick = () => {
    if (typeof window !== "undefined") {
      window.location.href = dashboardHref;
    }
  };

  return (
    <div
      ref={cardRef}
      onClick={handleClick}
      className="flex flex-col bg-gray-800/50 border border-gray-700 rounded-lg p-6 shadow-lg transition-all duration-200 card-enter cursor-pointer"
    >
      {/* Card Body */}
      <div className="flex-grow">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-lg font-semibold text-white">
            <a
              href={
                repository.html_url || `https://github.com/${repository.name}`
              }
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-400 transition-colors duration-200"
              onClick={(e) => e.stopPropagation()}
            >
              {repository.name}
            </a>
          </h3>
          {repository.language && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-900/50 text-blue-300 border border-blue-700/50">
              {repository.language}
            </span>
          )}
        </div>

        {/* Description */}
        <p className="text-gray-300 text-sm min-h-[40px] mb-4">
          {repository.description || "No description provided."}
        </p>
      </div>

      {/* Card Footer */}
      <div className="border-t border-gray-700 pt-4 flex items-center">
        <div className="flex items-center space-x-4 text-xs text-gray-400">
          <span className="capitalize">{repository.visibility}</span>
          <span>•</span>
          <span>{repository.default_branch}</span>
        </div>
        <span className="ml-auto text-xs text-gray-400">
          Updated {formatLastUpdated(repository.updated_at)}
        </span>
      </div>
    </div>
  );
}
