#!/usr/bin/env python3
"""
Git and GitHub Automation Starter Script

This script demonstrates how to use GitPython and PyGithub to:
- Perform local Git operations (status, add, commit, push)
- Interact with GitHub API (create issues, manage repositories)

Requirements:
    pip install GitPython PyGithub

Usage:
    1. Set the GITHUB_TOKEN environment variable (optional for some operations).
    2. Run the script: python git_github_starter.py
    3. The script will prompt you for the local repository path and GitHub repository name.
"""

from git import Repo, InvalidGitRepositoryError
from github import Github, GithubException
import os
import sys
import argparse

# --- Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def check_git_status_and_commit(repo_path, commit_message="Automated commit from script"):
    """
    Check Git status and commit changes if any exist.
    
    Args:
        repo_path (str): Path to the local Git repository
        commit_message (str): Commit message to use
    
    Returns:
        bool: True if changes were committed and pushed, False otherwise
    """
    try:
        repo = Repo(repo_path)
        
        # Check if there are changes to commit
        if repo.is_dirty(untracked_files=True):
            print("Git Status:")
            print(repo.git.status())
            print("-" * 50)
            
            # Add and commit changes
            repo.git.add(all=True)
            repo.index.commit(commit_message)
            print(f"Changes committed: {commit_message}")
            
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

def main():
    """
    Main function to orchestrate Git and GitHub operations.
    Prompts user for repository paths, validates them, and then performs operations.
    """
    
    # Check for GITHUB_TOKEN environment variable.
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN environment variable not set. GitHub API operations will be skipped.")
    
    # Note: Validations for local_repo_path and github_repo_name are now done
    # immediately after user input, using is_valid_git_repo and github_repo_exists.
    
    print("=== Git and GitHub Automation Script ===")
    print()

    local_repo_path_input = input("Enter the local Git repository path: ")
    if not is_valid_git_repo(local_repo_path_input):
        print("Exiting script due to invalid local repository path.")
        sys.exit(1)
        
    github_repo_name_input = input("Enter the GitHub repository name (e.g., username/repo): ")
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
