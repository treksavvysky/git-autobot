import Link from "next/link";
import { Repository } from "@/types/repository";

interface RepositoryCardProps {
  repository: Repository;
  token?: string;
}

export default function RepositoryCard({ repository, token }: RepositoryCardProps) {
  const readmeHref = token
    ? `/repositories/${encodeURIComponent(repository.name)}/readme?token=${encodeURIComponent(token)}`
    : `/repositories/${encodeURIComponent(repository.name)}/readme`;

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-6 border border-gray-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {repository.name}
          </h3>
          <p className="text-sm text-gray-600 mb-4">{repository.full_name}</p>
        </div>
        <div className="flex-shrink-0 ml-4 flex flex-col space-y-2">
          <a
            href={repository.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
          >
            View on GitHub
            <svg
              className="ml-2 -mr-1 w-4 h-4"
              fill="currentColor"
              viewBox="0 0 20 20"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                fillRule="evenodd"
                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </a>
          <Link
            href={readmeHref}
            className="inline-flex items-center justify-center px-4 py-2 border border-blue-600 text-sm font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
          >
            Display README
            <svg
              className="ml-2 -mr-1 w-4 h-4"
              fill="currentColor"
              viewBox="0 0 20 20"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                fillRule="evenodd"
                d="M4 3a1 1 0 011-1h10a1 1 0 011 1v14a1 1 0 01-1.555.832L10 14.333l-4.445 3.499A1 1 0 014 17V3z"
                clipRule="evenodd"
              />
            </svg>
          </Link>
        </div>
      </div>
    </div>
  );
}
