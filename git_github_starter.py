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

from git import Repo, InvalidGitRepositoryError, GitCommandError
from github import Github, GithubException
import os
import sys
import argparse
import re # Added re import
import json # For repository configuration management
from dotenv import load_dotenv


def _extract_name(obj, default=""):
    """Return a human readable name for ``obj``.

    Many tests provide ``MagicMock`` instances where ``name`` is not a simple
    attribute. This helper normalises those cases so printing behaviour is
    deterministic.
    """

    if obj is None:
        return default

    name = getattr(obj, "name", None)
    if isinstance(name, str) and name:
        return name

    # ``MagicMock`` stores the provided ``name`` in ``_mock_name``.
    mock_name = getattr(obj, "_mock_name", None)
    if isinstance(mock_name, str) and mock_name:
        return mock_name

    if name is not None:
        return str(name)

    return str(obj) if obj is not None else default

# Load environment variables from .env file if it exists
load_dotenv()

# --- Configuration ---
# GITHUB_TOKEN can be set as an environment variable or in a .env file.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- Repository Configuration Management ---
REPO_CONFIG_FILE = 'repo_config.json'

def load_repo_config():
    """
    Loads the repository configuration from REPO_CONFIG_FILE.
    The configuration is expected to be a dictionary where keys are aliases
    and values are dictionaries with repository details.
    Returns an empty dictionary if the file doesn't exist or an error occurs.
    """
    try:
        if os.path.exists(REPO_CONFIG_FILE):
            with open(REPO_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Basic validation for the new structure (optional, but good practice)
                if not isinstance(config, dict):
                    print(f"Warning: Configuration in {REPO_CONFIG_FILE} is not a dictionary.")
                    return {}
                for alias, details in config.items():
                    if not isinstance(details, dict) or "path" not in details:
                        print(f"Warning: Invalid entry for alias '{alias}' in {REPO_CONFIG_FILE}. Missing 'path' or not a dictionary.")
                        # Depending on strictness, you might want to skip this entry or return {}
                return config
        return {}
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading repository configuration: {e}")
        return {}

def save_repo_config(config):
    """
    Saves the given config dictionary (expected to follow the new structure)
    to REPO_CONFIG_FILE.
    """
    try:
        with open(REPO_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Repository configuration saved to {REPO_CONFIG_FILE}")
    except IOError as e:
        print(f"Error saving repository configuration: {e}")

def add_repo_to_config(alias, details):
    """
    Adds or updates a repository with the given alias and its details in the configuration.
    'details' must be a dictionary containing at least 'path'.
    Optional keys in 'details': 'branches' (list), 'url' (str), 'github_repo_name' (str).
    """
    if not isinstance(details, dict) or "path" not in details:
        print("Error: Repository details must be a dictionary and include a 'path'.")
        return

    config = load_repo_config()

    # Ensure optional keys are initialized if not provided
    repo_entry = {
        "path": details["path"],
        "branches": details.get("branches", []),
        "url": details.get("url"),
        "github_repo_name": details.get("github_repo_name")
    }

    config[alias] = repo_entry
    save_repo_config(config)
    print(f"Repository alias '{alias}' added/updated in config: {repo_entry}")

def get_repo_details_from_config(alias):
    """Return the stored repository details for ``alias`` if present."""

    config = load_repo_config()
    return config.get(alias)

def list_repos_from_config():
    """
    Lists all repositories stored in the configuration.
    """
    config = load_repo_config()
    if not config:
        print("No repositories found in the configuration.")
        return

    print("\n--- Stored Repositories ---")
    for alias, details in config.items():
        print(f"- Alias: {alias}")
        print(f"  Path: {details.get('path')}")
        if details.get('branches'):
            print(f"  Branches: {', '.join(details['branches'])}")
        if details.get('url'):
            print(f"  URL: {details['url']}")
        if details.get('github_repo_name'):
            print(f"  GitHub Repo: {details['github_repo_name']}")
        print("-" * 20) # Separator for readability
    print("--- End of Stored Repositories ---\n")

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

def create_github_repository(token, repo_name_full, description="", private=False):
    """
    Creates a new GitHub repository.

    Args:
        token (str): GitHub personal access token.
        repo_name_full (str): Full repository name in "username/reponame" format.
                              Only the 'reponame' part is used for creation under the authenticated user.
        description (str, optional): Description for the repository. Defaults to "".
        private (bool, optional): Whether the repository should be private. Defaults to False.

    Returns:
        github.Repository.Repository: The created repository object if successful, None otherwise.
    """
    if not token:
        print("Error: GitHub token is required to create a repository.")
        return None

    try:
        gh = Github(token)
        user = gh.get_user() # Get the authenticated user

        # Extract the actual repository name from "username/reponame"
        if '/' not in repo_name_full:
            actual_repo_name = repo_name_full # Assume it's just the repo name
        else:
            username, actual_repo_name = repo_name_full.split('/', 1)
            # We should ideally check if 'username' matches user.login, but create_repo works on the authenticated user context
            if username != user.login:
                print(f"Warning: Provided username '{username}' in '{repo_name_full}' does not match authenticated user '{user.login}'. Repository will be created under '{user.login}'.")

        print(f"Attempting to create GitHub repository: '{user.login}/{actual_repo_name}'")
        new_repo = user.create_repo(
            actual_repo_name,
            description=description,
            private=private,
            auto_init=False  # Set to True if you want GitHub to auto-initialize with a README
        )
        print(f"Successfully created GitHub repository: {new_repo.html_url}")
        return new_repo
    except GithubException as e:
        # Common statuses:
        # 422: Unprocessable Entity (often means repo already exists or name is invalid)
        # 401: Bad credentials (token invalid or lacks permissions)
        print(f"GitHub API error during repository creation for '{repo_name_full}': {e.status} {e.data}")
        if e.status == 422:
            print("This might mean the repository already exists or the name is invalid.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during repository creation for '{repo_name_full}': {e}")
        return None

def is_valid_git_repo(repo_path):
    """
    Checks if the given path is a valid Git repository.
    If not, asks the user if they want to initialize one.

    Args:
        repo_path (str): The file system path to check/initialize.

    Returns:
        tuple: (bool_is_valid_or_initialized, bool_was_newly_initialized)
               (True, False): Existing valid repo.
               (True, True): New repo, successfully initialized.
               (False, False): Invalid path, initialization failed or skipped.
    """
    try:
        Repo(repo_path)
        print(f"'{repo_path}' is already a Git repository.")
        return True, False # Valid, not newly initialized
    except InvalidGitRepositoryError:
        print(f"'{repo_path}' is not a valid Git repository.")
        user_choice = input(f"Do you want to initialize a new Git repository at '{repo_path}'? (y/n): ").lower()
        if user_choice == 'y':
            try:
                print(f"Initializing a new Git repository in '{repo_path}'...")
                repo = Repo.init(repo_path)
                print(f"Successfully initialized new Git repository in '{repo_path}'.")

                commit_choice = input("Do you want to make an initial commit? (y/n): ").lower()
                if commit_choice == 'y':
                    try:
                        # For a truly empty repo, need at least one file to commit.
                        # Creating a dummy .gitkeep file.
                        open(os.path.join(repo_path, ".gitkeep"), 'a').close()
                        repo.index.add([".gitkeep"])
                        repo.index.commit("Initial commit (created .gitkeep)")
                        print("Initial commit created successfully (added .gitkeep).")
                    except GitCommandError as commit_error:
                        print(f"Error creating initial commit: {commit_error}")
                        # Still consider repo initialized
                    except Exception as e_commit:
                        print(f"An unexpected error occurred during initial commit: {e_commit}")
                        # Still consider repo initialized
                else:
                    print("Skipping initial commit.")
                return True, True # Successfully initialized, was new
            except GitCommandError as init_error:
                print(f"Error initializing repository: {init_error}")
                return False, False
            except Exception as e_init:
                print(f"An unexpected error occurred during repository initialization: {e_init}")
                return False, False
        else:
            print("Repository initialization skipped by user.")
            return False, False
    except Exception as e:
        print(f"An unexpected error occurred while checking/initializing local repository: {e}")
        return False, False

def setup_remote_origin(local_repo_path, github_repo_url, default_branch_name="main"):
    """
    Sets up or updates the 'origin' remote for a local Git repository and pushes the default branch.

    Args:
        local_repo_path (str): Path to the local Git repository.
        github_repo_url (str): The URL of the GitHub repository (e.g., new_repo.clone_url).
        default_branch_name (str, optional): The name of the default branch to push. Defaults to "main".

    Returns:
        bool: True if setup and push were successful, False otherwise.
    """
    try:
        local_git_repo = Repo(local_repo_path)
        
        origin = None
        try:
            origin = local_git_repo.remote(name='origin')
        except ValueError: # GitPython raises ValueError if remote doesn't exist
            print(f"No remote named 'origin' found in '{local_repo_path}'. Creating one.")
        
        if origin:
            print(f"Remote 'origin' already exists in '{local_repo_path}'. Updating URL to '{github_repo_url}'.")
            with origin.config_writer as cw:
                cw.set("url", github_repo_url)
            print(f"Updated remote 'origin' URL to: {github_repo_url}")
        else:
            origin = local_git_repo.create_remote('origin', github_repo_url)
            print(f"Created remote 'origin' with URL: {github_repo_url}")

        if not local_git_repo.heads:
            print(f"Warning: Local repository at '{local_repo_path}' has no branches (no commits yet?). Cannot push.")
            print("Please ensure the local repository has an initial commit on the default branch.")
            return False
        
        # Ensure the specified default_branch_name actually exists locally.
        # The initial commit by is_valid_git_repo might be 'master' or 'main'.
        # We should push the *current* active branch if it's the one intended, or a specified one if it exists.
        
        local_branch_to_push = None
        try:
            # Check if the intended default_branch_name exists
            local_branch_to_push = local_git_repo.heads[default_branch_name]
            print(f"Found local branch '{default_branch_name}' to push.")
        except IndexError: # Branch by that name doesn't exist
            # If default_branch_name is not found, maybe the active branch is the one to push?
            # This can happen if local repo was init'd with 'master' but GitHub's default is 'main'.
            active_branch = local_git_repo.active_branch
            print(f"Warning: Branch '{default_branch_name}' not found locally. Attempting to push current active branch '{active_branch.name}'.")
            local_branch_to_push = active_branch
            default_branch_name = active_branch.name # Update to what we are actually pushing


        if not local_branch_to_push.commit:
             print(f"Error: Branch '{default_branch_name}' in '{local_repo_path}' has no commits. Cannot push.")
             return False

        print(f"Pushing local branch '{default_branch_name}' to 'origin' and setting upstream...")
        origin.push(refspec=f"{default_branch_name}:{default_branch_name}", set_upstream=True)
        print(f"Successfully pushed '{default_branch_name}' and set remote 'origin' as upstream.")
        return True
    except InvalidGitRepositoryError:
        print(f"Error: '{local_repo_path}' is not a valid Git repository.")
        return False
    except GitCommandError as e:
        print(f"Git command error during remote setup for '{local_repo_path}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during remote setup for '{local_repo_path}': {e}")
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

def clone_repository(github_token):
    """
    Clones a Git repository.

    The user can either provide a Git repository URL directly or choose from
    a list of their repositories on GitHub (if a token is provided).

    Args:
        github_token (str): GitHub personal access token. Can be None.

    Returns:
        str: The local path of the cloned repository if successful, otherwise None.
    """
    print("\n--- Clone Git Repository ---")
    clone_url = None
    repo_to_clone_name = None # For user feedback

    choice = input("Do you want to (1) provide a Git URL or (2) list your GitHub repositories to clone? (1/2): ").strip()

    if choice == '1':
        clone_url = input("Enter the Git repository URL to clone: ").strip()
        if not clone_url:
            print("No URL provided. Cloning aborted.")
            return None
        repo_to_clone_name = clone_url # Use URL as identifier for feedback
    elif choice == '2':
        if not github_token:
            print("GitHub token is required to list your repositories. Please set the GITHUB_TOKEN environment variable.")
            return None
        try:
            print("Fetching your GitHub repositories...")
            gh = Github(github_token)
            user = gh.get_user()
            repositories = list(user.get_repos()) # Get a list
            if not repositories:
                print("No repositories found on your GitHub account.")
                return None

            print("\nYour GitHub Repositories:")
            for i, repo in enumerate(repositories):
                print(f"{i + 1}. {repo.full_name}")

            while True:
                try:
                    selection = int(input("Select a repository to clone (enter number): "))
                    if 1 <= selection <= len(repositories):
                        selected_repo = repositories[selection - 1]
                        clone_url = selected_repo.clone_url
                        repo_to_clone_name = selected_repo.full_name
                        print(f"Selected repository: {repo_to_clone_name} ({clone_url})")
                        break
                    else:
                        print(f"Invalid selection. Please enter a number between 1 and {len(repositories)}.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        except GithubException as e:
            print(f"GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while fetching repositories: {e}")
            return None
    else:
        print("Invalid choice. Cloning aborted.")
        return None

    if not clone_url: # Should be set if either path 1 or 2 was successful
        print("Failed to determine repository URL. Cloning aborted.")
        return None

    local_clone_path = input(f"Enter the local path to clone '{repo_to_clone_name}' into: ").strip()
    if not local_clone_path:
        print("No local path provided. Cloning aborted.")
        return None

    try:
        print(f"Cloning '{repo_to_clone_name}' into '{local_clone_path}'...")
        Repo.clone_from(clone_url, local_clone_path)
        print(f"Repository '{repo_to_clone_name}' cloned successfully to '{local_clone_path}'.")
        return local_clone_path
    except GitCommandError as e:
        print(f"Error cloning repository: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during cloning: {e}")
        return None

def fetch_changes(repo_path, configured_branches=None):
    """Fetches changes from the 'origin' remote."""
    configured_branches = configured_branches or []
    try:
        print(f"\n--- Fetching changes for {repo_path} ---")
        repo = Repo(repo_path)
        origin = repo.remote(name='origin')
        if not origin.exists():
            print(f"Error: Remote 'origin' does not exist in {repo_path}.")
            return False
        
        fetch_info = origin.fetch()
        if not fetch_info:
            print("No fetch information returned. This might indicate no changes or an issue.")
        else:
            for info in fetch_info:
                name = _extract_name(info)
                summary = getattr(info, "summary", "")
                flags_value = getattr(info, "flags", 0)
                print(f"Fetched: {name}, Summary: {summary}, Flags: {flags_value}")

                error_flag = getattr(info, "ERROR", 0)
                rejected_flag = getattr(info, "REJECTED", 0)
                if isinstance(flags_value, int) and isinstance(error_flag, int) and flags_value & error_flag:
                    print(f"Error during fetch: {name} - {summary}")
                elif isinstance(flags_value, int) and isinstance(rejected_flag, int) and flags_value & rejected_flag:
                    print(f"Fetch rejected: {name} - {summary}")

        print("Fetch operation completed.")
        if configured_branches:
            print(f"Configured branches for this repository: {', '.join(configured_branches)}. "
                  "You may want to ensure these are up-to-date locally (e.g., by checking them out or pulling).")
        return True
    except InvalidGitRepositoryError:
        print(f"Error: {repo_path} is not a valid Git repository.")
        return False
    except GitCommandError as e:
        print(f"Git command error during fetch: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during fetch: {e}")
        return False

def list_branches(repo_path, configured_branches=None):
    """Lists local and remote branches, highlighting configured ones."""
    configured_branches = configured_branches or []
    try:
        print(f"\n--- Branches for {repo_path} ---")
        repo = Repo(repo_path)
        
        print("\nLocal branches:")
        if isinstance(repo.heads, dict):
            local_heads = list(repo.heads.values())
        elif isinstance(repo.heads, list):
            local_heads = list(repo.heads)
        else:
            try:
                local_heads = list(repo.heads)
            except TypeError:
                local_heads = []

        if not local_heads:
            print("  No local branches found.")
        else:
            for head in local_heads:
                head_name = _extract_name(head)
                marker = " * (in config)" if head_name in configured_branches else ""
                print(f"  - {head_name}{marker}")
        
        print("\nRemote branches (origin):")
        origin = repo.remote(name='origin')
        origin_name = _extract_name(origin, "origin")
        if not origin.exists():
            print("  Remote 'origin' does not exist.")
            return

        # Fetch to update remote refs before listing
        print("  (Fetching remote 'origin' to ensure list is up-to-date...)")
        origin.fetch()

        if isinstance(origin.refs, list):
            remote_refs = list(origin.refs)
        else:
            try:
                remote_refs = list(origin.refs)
            except TypeError:
                remote_refs = []
        if not remote_refs:
            print("  No remote branches found on 'origin'.")
        else:
            for ref in remote_refs:
                ref_name = _extract_name(ref)
                if ref_name == f"{origin_name}/HEAD":
                    continue
                simple_remote_branch_name = ref_name.split(f"{origin_name}/", 1)[-1]
                marker = " * (in config)" if simple_remote_branch_name in configured_branches else ""
                print(f"  - {ref_name}{marker}")
                for local_branch in local_heads:
                    tracking = None
                    try:
                        tracking = local_branch.tracking_branch()
                    except Exception:
                        tracking = None
                    tracking_name = _extract_name(tracking)
                    if tracking_name == ref_name:
                        local_name = _extract_name(local_branch)
                        local_marker = " * (in config)" if local_name in configured_branches else ""
                        print(f"    (tracked by local: {local_name}{local_marker})")
                        
    except InvalidGitRepositoryError:
        print(f"Error: {repo_path} is not a valid Git repository.")
    except GitCommandError as e:
        print(f"Git command error while listing branches: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while listing branches: {e}")


def _get_origin_url(repo_path):
    """Return the URL for the ``origin`` remote if configured."""

    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, Exception):
        return None

    try:
        origin = repo.remote(name="origin")
    except ValueError:
        return None

    return getattr(origin, "url", None)


def checkout_branch(repo_path, branch_name, create_new=False, configured_branches=None):
    """Checks out a branch, optionally creating it if new or tracking a remote."""
    configured_branches = configured_branches or []
    try:
        print(f"\n--- Checking out branch '{branch_name}' in {repo_path} ---")
        if branch_name in configured_branches:
            print(f"Note: '{branch_name}' is a configured branch for this repository.")

        repo = Repo(repo_path)
        
        if create_new:
            if branch_name in repo.heads:
                print(f"Error: Branch '{branch_name}' already exists. Cannot create.")
                return False
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            print(f"Created and checked out new branch: {branch_name}")
            return True

        # Try to checkout existing local branch
        if branch_name in repo.heads:
            print(f"Checking out existing local branch: {branch_name}")
            repo.heads[branch_name].checkout()
            print(f"Successfully checked out local branch: {branch_name}")
            return True

        # Try to checkout remote branch (e.g., origin/main as main)
        origin = repo.remote(name='origin')
        origin_name = _extract_name(origin, "origin")
        if not origin.exists():
            print("Error: Remote 'origin' not found. Cannot checkout remote branch.")
            return False

        remote_branch_name_full = branch_name
        if not branch_name.startswith(f"{origin_name}/"):
            remote_branch_name_full = f"{origin_name}/{branch_name}"

        # Check if the remote branch exists
        remote_ref_to_track = None
        for ref in origin.refs:
            if _extract_name(ref) == remote_branch_name_full:
                remote_ref_to_track = ref
                break

        if not remote_ref_to_track:
            print(f"Error: Branch '{branch_name}' not found as a local branch, and '{remote_branch_name_full}' not found on remote 'origin'.")
            print("Please fetch changes or check branch name.")
            if configured_branches:
                print(f"Configured branches for this alias are: {', '.join(configured_branches)}. Did you mean one of these?")
            return False

        # At this point, remote_ref_to_track is valid (e.g., origin.refs['main'] or origin.refs['feature/foo'])
        # Determine local name for the new tracking branch
        local_tracking_branch_name = getattr(remote_ref_to_track, "remote_head", None)
        if not local_tracking_branch_name:
            local_tracking_branch_name = remote_branch_name_full.split("/", 1)[-1]

        if local_tracking_branch_name in repo.heads:
            # Local branch with the target name already exists
            local_branch = repo.heads[local_tracking_branch_name]
            tracking = None
            try:
                tracking = local_branch.tracking_branch()
            except Exception:
                tracking = None
            tracking_name = _extract_name(tracking)
            remote_name = _extract_name(remote_ref_to_track)
            if tracking_name == remote_name:
                print(f"Local branch '{local_tracking_branch_name}' already tracks '{remote_name}'. Checking it out.")
                local_branch.checkout()
                print(f"Successfully checked out branch: {local_tracking_branch_name}")
                return True
            else:
                print(f"Error: Local branch '{local_tracking_branch_name}' exists but does not track '{remote_name}'.")
                print("Please resolve this manually (e.g., rename local branch or set tracking).")
                return False
        else:
            # Create new local branch tracking the remote one
            remote_name = _extract_name(remote_ref_to_track)
            print(f"Creating local branch '{local_tracking_branch_name}' to track remote branch '{remote_name}'.")
            new_tracking_branch = repo.create_head(local_tracking_branch_name, remote_ref_to_track)
            new_tracking_branch.set_tracking_branch(remote_ref_to_track) # Ensure tracking is set
            new_tracking_branch.checkout()
            print(f"Successfully created and checked out branch '{local_tracking_branch_name}' tracking '{remote_name}'.")
            return True
            
    except InvalidGitRepositoryError:
        print(f"Error: {repo_path} is not a valid Git repository.")
        return False
    except GitCommandError as e:
        print(f"Git command error during checkout: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during checkout: {e}")
        return False

def pull_changes(repo_path):
    """Pulls changes for the current branch from 'origin'."""
    try:
        print(f"\n--- Pulling changes for current branch in {repo_path} ---")
        repo = Repo(repo_path)
        
        if repo.is_dirty():
            print("Warning: Repository has uncommitted changes. Please commit or stash them before pulling.")
            # Optionally, you could offer to stash them here. For now, just warn.
            # return False # Or proceed with caution

        origin = repo.remote(name='origin')
        if not origin.exists():
            print("Error: Remote 'origin' not found. Cannot pull.")
            return False

        current_branch = repo.active_branch
        current_branch_name = _extract_name(current_branch, "current")
        try:
            tracking_branch = current_branch.tracking_branch()
        except Exception:
            tracking_branch = None

        if not tracking_branch:
            print(f"Error: Current branch '{current_branch_name}' is not tracking any remote branch. Cannot pull.")
            print(
                "Please set upstream for '{branch}' first (e.g., by pushing with --set-upstream or using `git branch --set-upstream-to=origin/{branch}`).".format(
                    branch=current_branch_name
                )
            )
            return False

        remote_name = getattr(tracking_branch, "remote_name", "origin")
        remote_head = getattr(tracking_branch, "remote_head", current_branch_name)
        print(f"Pulling changes from '{remote_name}/{remote_head}' into local branch '{current_branch_name}'...")
        # origin.pull() pulls the current *tracked* branch by default.
        # We can be more explicit if needed, but this should generally work if tracking is set.
        pull_info = origin.pull()

        if not pull_info:
            print("No pull information returned. This might mean no changes or an issue.")
        else:
            for info in pull_info:
                name = _extract_name(info)
                ref = getattr(info, "ref", "")
                summary = getattr(info, "summary", "")
                flags_value = getattr(info, "flags", 0)
                print(f"Pulled: {name}, Ref: {ref}, Summary: {summary}, Flags: {flags_value}")

                error_flag = getattr(info, "ERROR", 0)
                rejected_flag = getattr(info, "REJECTED", 0)
                no_change_flag = getattr(info, "NO_CHANGE", 0)
                ff_flag = getattr(info, "FAST_FORWARD", 0)
                merge_flag = getattr(info, "MERGE", 0)

                if isinstance(flags_value, int) and isinstance(error_flag, int) and flags_value & error_flag:
                    print(f"  Error during pull: {ref} - {summary}")
                elif isinstance(flags_value, int) and isinstance(rejected_flag, int) and flags_value & rejected_flag:
                    print(f"  Pull rejected: {ref} - {summary}")
                elif isinstance(flags_value, int) and isinstance(no_change_flag, int) and flags_value & no_change_flag:
                    print(f"  No changes for {ref}.")
                elif isinstance(flags_value, int) and (
                    (isinstance(ff_flag, int) and flags_value & ff_flag)
                    or (isinstance(merge_flag, int) and flags_value & merge_flag)
                ):
                    print(f"  Successfully updated {ref}.")


        print("Pull operation completed.")
        return True
    except InvalidGitRepositoryError:
        print(f"Error: {repo_path} is not a valid Git repository.")
        return False
    except GitCommandError as e:
        print(f"Git command error during pull: {e}")
        # Common errors: merge conflicts
        if "merge conflict" in str(e).lower():
            print("MERGE CONFLICT DETECTED. Please resolve conflicts manually.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during pull: {e}")
        return False

def main():
    """
    Main function to orchestrate Git and GitHub operations.
    """
    parser = argparse.ArgumentParser(description="Automate Git and GitHub operations.")

    parser.add_argument("--local-path", help="Path to the local Git repository. Used for existing repos or as destination for init/clone.")
    parser.add_argument("--github-repo", help="GitHub repository name (e.g., username/repo). Can be auto-detected or used for cloning.")
    parser.add_argument("--repo-alias", help="Alias of the repository from config to use (will load its details).")
    parser.add_argument("list_repos", nargs='?', const=True, default=False,
                        help="List all stored repository aliases and their details from config and exit.")
    
    # Arguments for adding a new repository to config
    add_repo_group = parser.add_argument_group('options for --add-new-repo')
    add_repo_group.add_argument("--add-new-repo", nargs='?', const="NO_ALIAS_PROVIDED_CONST",
                                help="Add a new repository to the configuration. Prompts for details if no alias is provided with the flag. "
                                     "Use with --repo-path, --repo-url, or --github-name to specify source.")
    
    source_group = add_repo_group.add_mutually_exclusive_group()
    source_group.add_argument("--repo-path", metavar="LOCAL_PATH", help="Path to an existing or new local Git repository.")
    source_group.add_argument("--repo-url", metavar="GIT_URL", help="Full Git URL (HTTPS or SSH) to clone.")
    source_group.add_argument("--github-name", metavar="USER/REPO", help="GitHub repository name (user/repo) to clone.")

    # General Git operations arguments
    parser.add_argument("--init-repo", action="store_true",
                        help="Initialize a new Git repository in the path specified by --local-path (or prompt if not set). "
                             "Note: If using --add-new-repo with --repo-path, initialization is handled there.")
    parser.add_argument("--clone-repo", action="store_true",
                        help="Clone a Git repository. Prompts for URL/GitHub selection and local path.")
    parser.add_argument("--create-github-repo", action="store_true", help="If specified, and the GitHub repository does not exist, attempt to create it.")
    # New arguments for fetch, branch, pull operations
    parser.add_argument("--fetch", action="store_true", help="Fetch changes from the 'origin' remote.")
    parser.add_argument("--list-branches", action="store_true", help="List local and remote branches.")
    parser.add_argument("--checkout", metavar="BRANCH_NAME", help="Checkout an existing local or remote branch. For remote, attempts to create a local tracking branch.")
    parser.add_argument("--create-branch", metavar="BRANCH_NAME", help="Create a new local branch and check it out.")
    parser.add_argument("--pull", action="store_true", help="Pull changes for the current tracked branch from 'origin'.")

    args = parser.parse_args()

    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN environment variable not set. GitHub API operations will be skipped for certain actions.")
    
    print("=== Git and GitHub Automation Script ===")

    if args.list_repos:
        list_repos_from_config()
        sys.exit(0)
        
    if args.add_new_repo is not None:
        repo_alias_to_add = None
        if args.add_new_repo == "NO_ALIAS_PROVIDED_CONST":
            repo_alias_to_add = input("Enter an alias for the new repository: ").strip()
        else:
            repo_alias_to_add = args.add_new_repo.strip()

        if not repo_alias_to_add:
            print("Error: Repository alias cannot be empty when using --add-new-repo.")
            sys.exit(1)
        
        repo_details = {"path": None, "branches": [], "url": None, "github_repo_name": None}

        if args.repo_path:
            repo_details["path"] = args.repo_path
            is_valid, _ = is_valid_git_repo(repo_details["path"])
            if not is_valid:
                print(f"Error: Path '{repo_details['path']}' is not a valid Git repository or could not be initialized. Aborting add.")
                sys.exit(1)
            
            repo_details["github_repo_name"] = get_github_repo_from_local(repo_details["path"])
            repo_details["url"] = _get_origin_url(repo_details["path"]) # Helper to get raw URL

        elif args.repo_url:
            repo_details["url"] = args.repo_url
            path_to_clone = input(f"Enter the local path to clone '{repo_alias_to_add}' ({repo_details['url']}) into: ").strip()
            if not path_to_clone:
                print("Error: Local path for cloning cannot be empty.")
                sys.exit(1)
            repo_details["path"] = path_to_clone
            try:
                print(f"Cloning '{repo_details['url']}' into '{repo_details['path']}'...")
                Repo.clone_from(repo_details["url"], repo_details["path"])
                print("Cloned successfully.")
                # Try to parse GitHub name from URL after successful clone
                repo_details["github_repo_name"] = get_github_repo_from_local(repo_details["path"])
            except GitCommandError as e:
                print(f"Error cloning repository: {e}")
                sys.exit(1)

        elif args.github_name:
            repo_details["github_repo_name"] = args.github_name
            # Default to HTTPS, could make this configurable
            repo_details["url"] = f"https://github.com/{args.github_name}.git"
            path_to_clone = input(f"Enter the local path to clone '{repo_alias_to_add}' ({repo_details['url']}) into: ").strip()
            if not path_to_clone:
                print("Error: Local path for cloning cannot be empty.")
                sys.exit(1)
            repo_details["path"] = path_to_clone
            try:
                print(f"Cloning '{repo_details['url']}' into '{repo_details['path']}'...")
                Repo.clone_from(repo_details["url"], repo_details["path"])
                print("Cloned successfully.")
            except GitCommandError as e:
                print(f"Error cloning repository: {e}")
                sys.exit(1)
        
        else: # No specific source flag, prompt user
            source_type = input("Is the repository local or remote? (local/remote): ").strip().lower()
            if source_type == "local":
                local_path = input(f"Enter the local path for '{repo_alias_to_add}': ").strip()
                if not local_path:
                    print("Error: Local path cannot be empty.")
                    sys.exit(1)
                repo_details["path"] = local_path
                is_valid, _ = is_valid_git_repo(repo_details["path"])
                if not is_valid:
                    print(f"Error: Path '{repo_details['path']}' is not a valid Git repository or could not be initialized. Aborting add.")
                    sys.exit(1)
                repo_details["github_repo_name"] = get_github_repo_from_local(repo_details["path"])
                repo_details["url"] = _get_origin_url(repo_details["path"])

            elif source_type == "remote":
                remote_identifier = input(f"Enter the Git URL or GitHub name (user/repo) for '{repo_alias_to_add}': ").strip()
                if not remote_identifier:
                    print("Error: Remote identifier cannot be empty.")
                    sys.exit(1)
                
                if remote_identifier.startswith("http") or remote_identifier.startswith("git@"):
                    repo_details["url"] = remote_identifier
                else: # Assume github_name
                    repo_details["github_repo_name"] = remote_identifier
                    repo_details["url"] = f"https://github.com/{remote_identifier}.git"

                path_to_clone = input(f"Enter the local path to clone '{repo_alias_to_add}' ({repo_details['url']}) into: ").strip()
                if not path_to_clone:
                    print("Error: Local path for cloning cannot be empty.")
                    sys.exit(1)
                repo_details["path"] = path_to_clone
                try:
                    print(f"Cloning '{repo_details['url']}' into '{repo_details['path']}'...")
                    Repo.clone_from(repo_details["url"], repo_details["path"])
                    print("Cloned successfully.")
                    # If URL was given, try to parse github name from it after clone
                    if not repo_details["github_repo_name"]:
                         repo_details["github_repo_name"] = get_github_repo_from_local(repo_details["path"])
                except GitCommandError as e:
                    print(f"Error cloning repository: {e}")
                    sys.exit(1)
            else:
                print("Invalid source type. Please enter 'local' or 'remote'.")
                sys.exit(1)

        # At this point, repo_details should be populated (path, url, github_repo_name).
        
        # Prompt for branches
        branches_input = input(f"Enter a comma-separated list of important branches for '{repo_alias_to_add}' (e.g., main,develop), or press Enter to skip: ").strip()
        if branches_input:
            repo_details["branches"] = [branch.strip() for branch in branches_input.split(',') if branch.strip()]
        else:
            repo_details["branches"] = []

        # Save to configuration
        add_repo_to_config(repo_alias_to_add, repo_details)
        # Script will then exit or continue if other operations were intended after adding a repo.
        # For now, adding a repo is an exclusive action if this block is entered.
        sys.exit(0)

    local_repo_path_input = None
    github_repo_name_input = None # Will be determined later
    repo_details_from_config = None # To store loaded repo details
    repo_just_created_or_cloned = False

    if args.clone_repo:
        cloned_path = clone_repository(GITHUB_TOKEN)
        if cloned_path:
            local_repo_path_input = cloned_path
            repo_just_created_or_cloned = True
            save_choice = input(f"Repository cloned to '{local_repo_path_input}'. Save to config? (y/n): ").lower()
            if save_choice == 'y':
                config_repo_alias = input("Enter an alias for this repository in the config: ").strip()
                if config_repo_alias:
                    # Basic details for a new clone
                    new_repo_details = {"path": local_repo_path_input}
                    # Try to get remote URL and github_repo_name if possible
                    try:
                        cloned_git_repo = Repo(local_repo_path_input)
                        if cloned_git_repo.remotes.origin:
                            new_repo_details["url"] = cloned_git_repo.remotes.origin.url
                            # Attempt to parse github_repo_name from URL
                            parsed_gh_name = get_github_repo_from_local(local_repo_path_input) # Pass path
                            if parsed_gh_name:
                                new_repo_details["github_repo_name"] = parsed_gh_name
                    except Exception as e:
                        print(f"Note: Could not automatically get URL/GitHub name for cloned repo: {e}")
                    add_repo_to_config(config_repo_alias, new_repo_details)
                else:
                    print("Invalid alias, not saving to config.")
        else:
            print("Cloning failed. Exiting.")
            sys.exit(1)

    if not local_repo_path_input and args.repo_alias:
        repo_details_from_config = get_repo_details_from_config(args.repo_alias)
        if repo_details_from_config:
            local_repo_path_input = repo_details_from_config.get("path")
            github_repo_name_input = repo_details_from_config.get("github_repo_name")
            branches_from_config = repo_details_from_config.get("branches", []) # Get branches
            print(f"Using repository alias '{args.repo_alias}' from config.")
            print(f"  Path: {local_repo_path_input}")
            if github_repo_name_input:
                print(f"  GitHub Repo Name: {github_repo_name_input}")
            if branches_from_config: # Use the extracted variable
                print(f"  Configured branches: {', '.join(branches_from_config)}")
        else:
            print(f"Error: Repository alias '{args.repo_alias}' not found in config. Exiting.")
            sys.exit(1)
    else: # Not using --repo-alias, so no configured branches from this source
        branches_from_config = []


    if not local_repo_path_input:
        if args.local_path:
            local_repo_path_input = args.local_path
            print(f"Using local path from command line: {local_repo_path_input}")
        else:
            # Prompt only if not init-repo or clone-repo (clone handles its own path prompt)
            if not args.init_repo and not args.clone_repo : # clone-repo already handled
                 local_repo_path_input = input("Enter the local Git repository path: ").strip()
            elif args.init_repo : # for init-repo, if no path specified, prompt is needed
                 local_repo_path_input = input("Enter the path for the new Git repository: ").strip()


    if not local_repo_path_input: # If path is still not determined (e.g. user provided empty input)
        # Check if we are in an init-repo context, because is_valid_git_repo will prompt again if path is empty
        # However, is_valid_git_repo expects a path.
        if args.init_repo and not local_repo_path_input:
             print("Error: A local path is required to initialize a repository. Exiting.")
             sys.exit(1)
        elif not args.clone_repo: # clone_repo handles its own exit if path is not provided
            print("Error: Local repository path not specified. Exiting.")
            sys.exit(1)
        # If clone_repo was specified but somehow local_repo_path_input is still None here, it means cloning failed.
        # This case should have been handled by the clone_repo block's sys.exit(1).

    # Validate local repository path (this will also handle initialization if needed)
    # The args.init_repo flag primarily ensures that a path is obtained if not provided for initialization.
    # is_valid_git_repo itself prompts for initialization if the path is not a repo.
    is_valid, was_newly_initialized = is_valid_git_repo(local_repo_path_input)

    if not is_valid:
        print(f"Failed to validate or initialize repository at '{local_repo_path_input}'. Exiting.")
        sys.exit(1)

    if was_newly_initialized and not repo_just_created_or_cloned : # Don't ask again if just cloned and saved
        repo_just_created_or_cloned = True # Mark true to avoid re-prompting if script logic changes
        save_choice = input(f"New repository initialized at '{local_repo_path_input}'. Save to config? (y/n): ").lower()
        if save_choice == 'y':
            config_repo_alias = input("Enter an alias for this new repository in the config: ").strip()
            if config_repo_alias:
                # Basic details for a new repo
                new_repo_details = {"path": local_repo_path_input}
                # User might want to add more details later (URL, GitHub name) via a dedicated config management command
                add_repo_to_config(config_repo_alias, new_repo_details)
            else:
                print("Invalid alias, not saving to config.")

    # Determine GitHub repository name if not already loaded from config
    if not github_repo_name_input: # Was not set by --repo-alias and loading from config
        if args.github_repo:
            github_repo_name_input = args.github_repo
            print(f"Using GitHub repo name from command line: {github_repo_name_input}")
        else:
            print("Attempting to automatically determine GitHub repository name from local git config...")
            # Ensure local_repo_path_input is valid before passing to get_github_repo_from_local
            if local_repo_path_input and os.path.exists(local_repo_path_input):
                 github_repo_name_input = get_github_repo_from_local(local_repo_path_input)
                 if github_repo_name_input:
                     print(f"Auto-detected GitHub repository name: {github_repo_name_input}")
                 else:
                     print("Could not auto-detect GitHub repository name.")
            else:
                print(f"Local path '{local_repo_path_input}' is not valid for auto-detection of GitHub repo name.")

            if not github_repo_name_input: # If still not found
                 github_repo_name_input = input("Enter the GitHub repository name (e.g., username/repo): ").strip()
    
    # If github_repo_name_input was loaded from config, it might be None.
    # If it's None AND not provided by other means, then prompt or error.
    if not github_repo_name_input and not args.create_github_repo : # If we intend to create one, name can be specified now
         print("Warning: GitHub repository name not determined (not in config for alias, not auto-detected, not via --github-repo).")
         user_choice_gh_name = input("Do you want to specify a GitHub repository name now? (e.g., username/repo) or skip GitHub operations [s]kip? ").strip()
         if user_choice_gh_name.lower() == 's' or not user_choice_gh_name:
             print("Skipping GitHub-specific operations as no GitHub repository name was provided.")
             # GITHUB_TOKEN = None # Effectively disable GitHub ops if user skips providing a name
         else:
             github_repo_name_input = user_choice_gh_name

    # Final check for github_repo_name_input before operations that require it
    if not github_repo_name_input and (args.create_github_repo or GITHUB_TOKEN): # Check if needed for other ops
        # Allow proceeding if only local operations are intended and no github_repo_name_input was found/given
        if not (args.fetch or args.list_branches or args.checkout or args.create_branch or args.pull or args.local_path):
             print("Error: GitHub repository name is required for further GitHub operations (e.g. creation, API calls). Exiting.")
             sys.exit(1)
        elif GITHUB_TOKEN : # If token is there, but name is missing, it's likely an issue for GH ops
             print("Warning: GitHub repository name not specified. Some GitHub operations might fail if attempted.")


    # --- Automatic Save for New Repos (if not using --add-new-repo) ---
    # This section is placed after all opportunities for local_repo_path_input and github_repo_name_input
    # to be determined (including clone, init, or loading from args/config).
    if not args.add_new_repo and local_repo_path_input: # Ensure path is known
        current_config = load_repo_config()
        is_known_repo = False
        for alias, details in current_config.items():
            if details.get("path") == local_repo_path_input:
                is_known_repo = True
                # print(f"Debug: Repo path {local_repo_path_input} found in config under alias '{alias}'.")
                break
            if github_repo_name_input and details.get("github_repo_name") == github_repo_name_input:
                is_known_repo = True
                # print(f"Debug: GitHub name {github_repo_name_input} found in config under alias '{alias}'.")
                break
        
        if not is_known_repo:
            display_name = github_repo_name_input if github_repo_name_input else local_repo_path_input
            user_choice_save = input(f"\nThe repository '{display_name}' is not yet in your configuration. Would you like to add it? (y/n): ").strip().lower()
            if user_choice_save == 'y':
                new_alias = input("Enter an alias for this repository (e.g., project-name-api): ").strip()
                if not new_alias:
                    print("Alias cannot be empty. Skipping save.")
                else:
                    new_repo_details = {"path": local_repo_path_input}
                    if github_repo_name_input:
                        new_repo_details["github_repo_name"] = github_repo_name_input
                    
                    # Attempt to get URL if not already via github_repo_name_input (which implies a github url)
                    if not new_repo_details.get("url") and local_repo_path_input:
                        new_repo_details["url"] = _get_origin_url(local_repo_path_input)

                    branches_input = input(f"Enter a comma-separated list of important branches for '{new_alias}' (e.g., main,develop), or press Enter to skip: ").strip()
                    if branches_input:
                        new_repo_details["branches"] = [branch.strip() for branch in branches_input.split(',') if branch.strip()]
                    else:
                        new_repo_details["branches"] = []
                    
                    add_repo_to_config(new_alias, new_repo_details)
            else:
                print(f"Repository '{display_name}' will not be added to the configuration for this session.")

    # --- GitHub Repository Existence and Creation (if applicable) ---
    # This part should only run if a github_repo_name_input is available AND relevant operations are intended
    if github_repo_name_input and (GITHUB_TOKEN or args.create_github_repo): # Ensure it's relevant to check/create
        repo_exists_on_github = github_repo_exists(GITHUB_TOKEN, github_repo_name_input)

        if not repo_exists_on_github:
            if args.create_github_repo:
                if not GITHUB_TOKEN:
                    print("Error: --create-github-repo requires GITHUB_TOKEN to be set. Exiting.")
                sys.exit(1)
            
            print(f"Attempting to create GitHub repository '{github_repo_name_input}' as per --create-github-repo flag.")
            # You might want to gather description from user or args
            repo_description = f"Repository {github_repo_name_input} created by git_github_starter.py" 
            created_repo_obj = create_github_repository(
                GITHUB_TOKEN, 
                github_repo_name_input, 
                description=repo_description, # Pass a description
                private=False # Default to public, could be an arg
            )

            if created_repo_obj:
                print(f"Repository '{created_repo_obj.full_name}' created successfully on GitHub: {created_repo_obj.html_url}")
                
                # Determine current local branch name to push
                try:
                    local_git_repo_for_branch_check = Repo(local_repo_path_input)
                    # Ensure there's at least one commit, otherwise active_branch might error or be unexpected
                    if not local_git_repo_for_branch_check.head.is_valid() or not local_git_repo_for_branch_check.active_branch.commit:
                        print(f"Error: Local repository at '{local_repo_path_input}' has no commits on the current branch.")
                        print("Please make an initial commit before trying to push to a new GitHub repository.")
                        sys.exit(1)
                    current_local_branch_name = local_git_repo_for_branch_check.active_branch.name
                except Exception as e:
                    print(f"Critical: Could not determine active local branch from '{local_repo_path_input}': {e}")
                    print("This usually means the local repository is not in a valid state (e.g., no commits).")
                    sys.exit(1)

                print(f"Now setting up local remote 'origin' to '{created_repo_obj.clone_url}' and pushing branch '{current_local_branch_name}'.")
                setup_success = setup_remote_origin(
                    local_repo_path_input, 
                    created_repo_obj.clone_url, 
                    default_branch_name=current_local_branch_name
                )
                if not setup_success:
                    print(f"Failed to set up remote 'origin' for '{local_repo_path_input}' or push initial content.")
                    print(f"The GitHub repository '{created_repo_obj.html_url}' was created, but you may need to manually set up the remote and push.")
                    sys.exit(1) 
                print(f"Successfully set up remote 'origin' and pushed '{current_local_branch_name}'.")
                # Update github_repo_name_input to the full name from the created repo object to ensure consistency
                github_repo_name_input = created_repo_obj.full_name 
            else:
                print(f"Failed to create GitHub repository '{github_repo_name_input}'. Please check logs. Exiting.")
                sys.exit(1)
        else:
            # This is the original behavior: repo doesn't exist and user didn't ask to create it.
            print(f"Error: GitHub repository '{github_repo_name_input}' not found or not accessible, and --create-github-repo not specified. Exiting.")
            sys.exit(1)
    
    print(f"\nProceeding with operations for local repo: '{local_repo_path_input}' and GitHub repo: '{github_repo_name_input}'\n")

    # --- Local Git Operations ---
    print("1. Checking local Git repository status...")
    changes_made = check_git_status_and_commit(local_repo_path_input)
    print()
    
    # --- GitHub API Operations ---
    if GITHUB_TOKEN and not (args.fetch or args.list_branches or args.checkout or args.create_branch or args.pull):
        # Only run these if no other specific git operation was requested that might not need full GitHub API interaction immediately
        # Or, adjust this logic if these info/issue creation steps are desired alongside other ops.
        print("2. Getting GitHub repository information...")
        get_repository_info(GITHUB_TOKEN, github_repo_name_input)
        print()
        
        if changes_made: # Optionally create an issue if changes were made and pushed
            print("3. Creating GitHub issue for the changes...")
            create_github_issue(
                GITHUB_TOKEN,
                github_repo_name_input,
                "Automated Update via Script",
                "This issue was created automatically after changes were pushed by the script.",
                ["automation", "script-update"]
            )
    elif not GITHUB_TOKEN and not (args.fetch or args.list_branches or args.checkout or args.create_branch or args.pull):
        print("Skipping GitHub API operations (GITHUB_TOKEN not set).")

    # --- Additional Git Operations based on new flags ---
    if args.fetch:
        fetch_changes(local_repo_path_input, configured_branches=branches_from_config)

    if args.list_branches:
        list_branches(local_repo_path_input, configured_branches=branches_from_config)

    if args.create_branch:
        # For create_branch, configured_branches might be less relevant for the action itself,
        # but could be passed if checkout_branch is internally called and benefits from it.
        # Current implementation of checkout_branch does not use it if create_new is True.
        checkout_branch(local_repo_path_input, args.create_branch, create_new=True, configured_branches=branches_from_config)
    elif args.checkout:
        checkout_branch(local_repo_path_input, args.checkout, configured_branches=branches_from_config)
    
    # Pull operation should ideally be after any checkout or branch creation
    if args.pull:
        pull_changes(local_repo_path_input) # configured_branches not directly used by pull_changes current logic
    
    print("\n=== Script completed successfully ===")

if __name__ == "__main__":
    main()
