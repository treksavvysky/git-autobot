#!/usr/bin/env python3
"""
Git and GitHub Automation Starter Script

This script demonstrates how to use GitPython and PyGithub to:
- Perform local Git operations (status, add, commit, push)
- Interact with GitHub API (create issues, manage repositories)

Requirements:
    pip install GitPython PyGithub python-dotenv

Setup & Usage:

1.  **GitHub Token (`GITHUB_TOKEN`):**
    *   This token is required for GitHub API operations (e.g., creating issues, getting repo info).
    *   Set it as an environment variable OR create a `.env` file in the script's directory
      with the line: `GITHUB_TOKEN=your_personal_access_token`
    *   If not set, GitHub operations will be skipped.

2.  **Running the Script:**
    `python git_github_starter.py [options]`

3.  **Repository Information (Local Path & GitHub Repo Name):**
    The script determines the local repository path and GitHub repository name using the following order of precedence:

    *   **Command-Line Arguments (Highest Precedence):**
        *   `--local-path PATH`: Specify the path to your local Git repository.
        *   `--github-repo USER/REPO`: Specify the GitHub repository name (e.g., `username/repository`).
        If a command-line argument is provided for a piece of information, it will be used.

    *   **Automatic Detection (for GitHub Repo Name only):**
        *   If `--github-repo` is NOT provided, the script will attempt to automatically determine
          the GitHub repository name from the 'origin' remote URL of the local Git repository
          (specified by `--local-path` or prompted).

    *   **Interactive Prompts (Lowest Precedence):**
        *   If the local path is not provided via `--local-path`, the script will prompt you to enter it.
        *   If the GitHub repository name is not provided via `--github-repo` AND cannot be
          auto-detected, the script will prompt you to enter it.
"""

from git import Repo, InvalidGitRepositoryError
from github import Github, GithubException
import os
import sys
import argparse
import re # Added re import
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# --- Configuration ---
# GITHUB_TOKEN can be set as an environment variable or in a .env file.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def check_git_status_and_commit(repo_path):
    """
    Checks the Git status of the repository at `repo_path`.
    If changes are detected, it displays the status, then prompts the user
    for confirmation (y/n) to proceed with staging and committing.
    If confirmed, it prompts for a custom commit message. If the user provides
    an empty commit message, a default message is used.
    Finally, it stages all changes, commits them with the provided or default
    message, and pushes them to the 'origin' remote.

    Args:
        repo_path (str): Path to the local Git repository.
    
    Returns:
        bool: True if changes were successfully committed and pushed,
              False otherwise (e.g., no changes, commit aborted by user, or an error occurred).
    """
    try:
        repo = Repo(repo_path)
        
        # Check if there are changes to commit
        if repo.is_dirty(untracked_files=True):
            print("\n--- Git Status ---")
            status_output = repo.git.status()
            print(status_output)
            print("--- End Git Status ---\n")

            confirmation = input("Do you want to stage and commit these changes? (y/n): ").lower()
            if confirmation != 'y':
                print("Commit aborted by user.")
                return False
            
            # Add all changes (staging)
            repo.git.add(all=True)

            # Prompt for user-defined commit message
            user_commit_message = input("Enter commit message: ")
            if not user_commit_message.strip():
                user_commit_message = "Automated commit from script (user approved, no message provided)"
                print(f"Empty commit message provided. Using default: '{user_commit_message}'")

            repo.index.commit(user_commit_message)
            print(f"Changes committed with message: '{user_commit_message}'")
            
            # Push changes
            origin = repo.remote(name='origin')
            origin.push()
            print("Changes pushed to GitHub.")
            return True
        else:
            print("No changes to commit.")
            return False
            
    except InvalidGitRepositoryError:
        print(f"Error: {repo_path} is not a valid Git repository")
        return False
    except Exception as e:
        print(f"Git operation error: {e}")
        return False

def create_github_issue(token, repo_name, title, body, labels=None):
    """
    Create an issue on GitHub.
    
    Args:
        token (str): GitHub personal access token
        repo_name (str): Repository name in format "username/repo"
        title (str): Issue title
        body (str): Issue body/description
        labels (list): List of label names to apply
    
    Returns:
        str: URL of created issue, or None if failed
    """
    try:
        gh = Github(token)
        gh_repo = gh.get_repo(repo_name)
        
        # Create issue
        issue = gh_repo.create_issue(
            title=title,
            body=body,
            labels=labels or []
        )
        
        print(f"Issue created: {issue.html_url}")
        return issue.html_url
        
    except GithubException as e:
        print(f"GitHub API error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected GitHub error: {e}")
        return None

def get_repository_info(token, repo_name):
    """
    Get basic information about a GitHub repository.
    
    Args:
        token (str): GitHub personal access token
        repo_name (str): Repository name in format "username/repo"
    """
    try:
        gh = Github(token)
        repo = gh.get_repo(repo_name)
        
        print(f"Repository: {repo.full_name}")
        print(f"Description: {repo.description}")
        print(f"Stars: {repo.stargazers_count}")
        print(f"Forks: {repo.forks_count}")
        print(f"Open Issues: {repo.open_issues_count}")
        print(f"Default Branch: {repo.default_branch}")
        print(f"Last Updated: {repo.updated_at}")
        
    except GithubException as e:
        print(f"GitHub API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def is_valid_git_repo(repo_path):
    from git import Repo, InvalidGitRepositoryError # Moved import here
    """
    Checks if the given path is a valid Git repository.

    Args:
        repo_path (str): The file system path to check.
    
    Returns:
        bool: True if `repo_path` is a valid Git repository, False otherwise.
    """
    try:
        Repo(repo_path)
        return True
    except InvalidGitRepositoryError:
        print(f"Error: {repo_path} is not a valid Git repository.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while checking local repository: {e}")
        return False

def github_repo_exists(github_token, repo_name):
    """
    Checks if a GitHub repository exists and is accessible using the provided token.

    Args:
        github_token (str): GitHub personal access token. Can be None or empty.
        repo_name (str): The full name of the repository (e.g., "username/repo").

    Returns:
        bool: True if the repository exists and is accessible.
              Also returns True if `github_token` is not provided (skipping the check).
              Returns False if the repository is not found, or another API error occurs.
    """
    from github import Github, GithubException # Local import

    if not github_token:
        print("Warning: GITHUB_TOKEN environment variable not set. Skipping GitHub repository existence check.")
        return True # Treat as success if no token, allowing local-only operations or if repo interaction is optional.

    try:
        gh = Github(github_token)
        gh.get_repo(repo_name)
        print(f"GitHub repository '{repo_name}' found and accessible.")
        return True
    except GithubException as e:
        if e.status == 404:
            print(f"Error: GitHub repository '{repo_name}' not found or token lacks permissions. Status: {e.status}")
        else:
            print(f"GitHub API error while checking repository '{repo_name}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while checking GitHub repository '{repo_name}': {e}")
        return False

def get_github_repo_from_local(local_repo_path):
    """
    Attempts to determine the GitHub repository name (username/reponame)
    from the local Git repository's 'origin' remote URL.

    Args:
        local_repo_path (str): Path to the local Git repository.

    Returns:
        str: The 'username/reponame' if successfully extracted, otherwise None.
    """
    from git import Repo # Local import for self-containment
    try:
        repo = Repo(local_repo_path)
        if not repo.remotes:
            print("Info: No remotes found in the local repository.")
            return None

        origin = None
        for remote in repo.remotes:
            if remote.name == "origin":
                origin = remote
                break

        if not origin:
            print("Info: No remote named 'origin' found.")
            return None

        url = origin.url
        # Regex to capture username/reponame from SSH or HTTPS URLs
        # Handles URLs like:
        # - git@github.com:username/reponame.git
        # - https://github.com/username/reponame.git
        # - git@github.com:username/reponame
        # - https://github.com/username/reponame
        match = re.search(r'(?:[:/])([\w.-]+/[\w.-]+?)(?:\.git)?$', url)
        if match:
            return match.group(1)
        else:
            print(f"Info: Could not parse GitHub repository name from URL: {url}")
            return None
    except InvalidGitRepositoryError: # Should be caught by is_valid_git_repo earlier
        print(f"Error: {local_repo_path} is not a valid Git repository (should have been caught earlier).")
        return None
    except Exception as e:
        print(f"Error extracting GitHub repo name from local config: {e}")
        return None

def main():
    """
    Main function to orchestrate Git and GitHub operations.
    Orchestrates the script's operations:
    1. Parses command-line arguments.
    2. Checks for the GITHUB_TOKEN.
    3. Determines the local repository path (from args or prompt).
    4. Validates the local repository path.
    5. Determines the GitHub repository name (from args, auto-detection, or prompt).
    6. Validates the GitHub repository name and its accessibility.
    7. Executes Git operations (status, commit, push if changes).
    8. Executes GitHub API operations (get info, create issue if changes and token available).
    """
    parser = argparse.ArgumentParser(description="Automate Git and GitHub operations.")
    parser.add_argument("--local-path", help="Path to the local Git repository.")
    parser.add_argument("--github-repo", help="GitHub repository name (e.g., username/repo).")
    args = parser.parse_args()

    # Check for GITHUB_TOKEN environment variable (loaded from .env or environment).
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN environment variable not set. GitHub API operations will be skipped.")
    
    print("=== Git and GitHub Automation Script ===")
    print()

    # Determine local repository path: command-line arg > prompt.
    if args.local_path:
        local_repo_path_input = args.local_path
        print(f"Using local path from command line: {local_repo_path_input}")
    else:
        local_repo_path_input = input("Enter the local Git repository path: ")

    # Validate local repository path.
    if not is_valid_git_repo(local_repo_path_input):
        print("Exiting script due to invalid local repository path.")
        sys.exit(1)

    # Determine GitHub repository name: command-line arg > auto-detection > prompt.
    if args.github_repo:
        github_repo_name_input = args.github_repo
        print(f"Using GitHub repo name from command line: {github_repo_name_input}")
    else:
        print("Attempting to automatically determine GitHub repository name from local git config...")
        github_repo_name_input = get_github_repo_from_local(local_repo_path_input)
        if github_repo_name_input:
            print(f"Auto-detected GitHub repository name: {github_repo_name_input}")
        else:
            print("Could not auto-detect GitHub repository name.")
            github_repo_name_input = input("Enter the GitHub repository name (e.g., username/repo): ")

    # Ensure GitHub repository name is provided.
    if not github_repo_name_input:
        print("Error: GitHub repository name is required.")
        sys.exit(1)

    # Validate GitHub repository existence and accessibility.
    if not github_repo_exists(GITHUB_TOKEN, github_repo_name_input):
        print("Exiting script due to invalid GitHub repository or access issues.")
        sys.exit(1)
    
    # --- Local Git Operations ---
    print("1. Checking local Git repository...")
    changes_made = check_git_status_and_commit(local_repo_path_input)
    print()
    
    # --- GitHub API Operations ---
    if GITHUB_TOKEN:
        print("2. Getting repository information...")
        get_repository_info(GITHUB_TOKEN, github_repo_name_input)
        print()
        
        # Optionally create an issue if changes were made
        if changes_made:
            print("3. Creating GitHub issue for the changes...")
            issue_url = create_github_issue(
                GITHUB_TOKEN,
                github_repo_name_input,
                "Automated Update",
                "This issue was created automatically after pushing changes to the repository.",
                ["automation", "script-generated"]
            )
    else:
        print("2. Skipping GitHub API operations (no token provided)")
    
    print("\n=== Script completed ===")

if __name__ == "__main__":
    main()
