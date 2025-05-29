#!/usr/bin/env python3
"""
Git and GitHub Automation Starter Script

This script demonstrates how to use GitPython and PyGithub to:
- Perform local Git operations (status, add, commit, push)
- Interact with GitHub API (create issues, manage repositories)

Requirements:
    pip install GitPython PyGithub

Usage:
    1. Set GITHUB_TOKEN environment variable
    2. Update the config variables below
    3. Run the script: python git_github_starter.py
"""

from git import Repo, InvalidGitRepositoryError
from github import Github, GithubException
import os
import sys

# --- Configuration ---
LOCAL_REPO_PATH = "/path/to/your/local/repo"  # Update this path
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_NAME = "your-username/your-repo-name"  # Update this

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

def main():
    """Main function to demonstrate Git and GitHub operations."""
    
    # Validate configuration
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN environment variable not set.")
        print("GitHub API operations will be skipped.")
    
    if LOCAL_REPO_PATH == "/path/to/your/local/repo":
        print("Please update LOCAL_REPO_PATH in the configuration section.")
        return
    
    if GITHUB_REPO_NAME == "your-username/your-repo-name":
        print("Please update GITHUB_REPO_NAME in the configuration section.")
        return
    
    print("=== Git and GitHub Automation Script ===")
    print()
    
    # --- Local Git Operations ---
    print("1. Checking local Git repository...")
    changes_made = check_git_status_and_commit(LOCAL_REPO_PATH)
    print()
    
    # --- GitHub API Operations ---
    if GITHUB_TOKEN:
        print("2. Getting repository information...")
        get_repository_info(GITHUB_TOKEN, GITHUB_REPO_NAME)
        print()
        
        # Optionally create an issue if changes were made
        if changes_made:
            print("3. Creating GitHub issue for the changes...")
            issue_url = create_github_issue(
                GITHUB_TOKEN,
                GITHUB_REPO_NAME,
                "Automated Update",
                "This issue was created automatically after pushing changes to the repository.",
                ["automation", "script-generated"]
            )
    else:
        print("2. Skipping GitHub API operations (no token provided)")
    
    print("\n=== Script completed ===")

if __name__ == "__main__":
    main()
