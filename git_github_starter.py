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
    Returns an empty dictionary if the file doesn't exist or an error occurs.
    """
    try:
        if os.path.exists(REPO_CONFIG_FILE):
            with open(REPO_CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading repository configuration: {e}")
        return {}

def save_repo_config(config):
    """
    Saves the given config dictionary to REPO_CONFIG_FILE.
    """
    try:
        with open(REPO_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Repository configuration saved to {REPO_CONFIG_FILE}")
    except IOError as e:
        print(f"Error saving repository configuration: {e}")

def add_repo_to_config(name, path):
    """
    Adds or updates a repository name and its path in the configuration.
    """
    config = load_repo_config()
    config[name] = path
    save_repo_config(config)
    print(f"Repository '{name}' (path: '{path}') added/updated in config.")

def get_repo_path_from_config(name):
    """
    Retrieves the path for a given repository name from the configuration.
    Returns None if the name is not found.
    """
    config = load_repo_config()
    return config.get(name)

def list_repos_from_config():
    """
    Lists all repositories stored in the configuration.
    """
    config = load_repo_config()
    if not config:
        print("No repositories found in the configuration.")
        return

    print("\n--- Stored Repositories ---")
    for name, path in config.items():
        print(f"- Name: {name}, Path: {path}")
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
    from git import Repo, InvalidGitRepositoryError, GitCommandError  # Moved import here and added GitCommandError
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

def fetch_changes(repo_path):
    """Fetches changes from the 'origin' remote."""
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
                print(f"Fetched: {info.name}, Summary: {info.summary}, Flags: {info.flags}")
                if info.flags & info.ERROR:
                    print(f"Error during fetch: {info.name} - {info.summary}")
                elif info.flags & info.REJECTED:
                     print(f"Fetch rejected: {info.name} - {info.summary}")

        print("Fetch operation completed.")
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

def list_branches(repo_path):
    """Lists local and remote branches."""
    try:
        print(f"\n--- Branches for {repo_path} ---")
        repo = Repo(repo_path)
        
        print("\nLocal branches:")
        if not repo.heads:
            print("  No local branches found.")
        else:
            for head in repo.heads:
                print(f"  - {head.name}")
        
        print("\nRemote branches (origin):")
        origin = repo.remote(name='origin')
        if not origin.exists():
            print("  Remote 'origin' does not exist.")
            return

        # Fetch to update remote refs before listing
        print("  (Fetching remote 'origin' to ensure list is up-to-date...)")
        origin.fetch()

        if not origin.refs:
            print("  No remote branches found on 'origin'.")
        else:
            for ref in origin.refs:
                # ref.name is like 'origin/main', 'origin/feature/branch'
                # We don't want to list 'origin/HEAD'
                if ref.name == f"{origin.name}/HEAD":
                    continue
                print(f"  - {ref.name}")
                # You could also show tracking information if a local branch tracks this remote ref
                for local_branch in repo.heads:
                    if local_branch.tracking_branch() and local_branch.tracking_branch().name == ref.name:
                        print(f"    (tracked by local: {local_branch.name})")
                        
    except InvalidGitRepositoryError:
        print(f"Error: {repo_path} is not a valid Git repository.")
    except GitCommandError as e:
        print(f"Git command error while listing branches: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while listing branches: {e}")

def checkout_branch(repo_path, branch_name, create_new=False):
    """Checks out a branch, optionally creating it if new or tracking a remote."""
    try:
        print(f"\n--- Checking out branch '{branch_name}' in {repo_path} ---")
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
        if not origin.exists():
            print("Error: Remote 'origin' not found. Cannot checkout remote branch.")
            return False

        remote_branch_name_full = branch_name # e.g. user provides "main" intending "origin/main"
        if not branch_name.startswith(f"{origin.name}/"):
             remote_branch_name_full = f"{origin.name}/{branch_name}" # e.g. "origin/main"

        # Check if the remote branch exists
        remote_ref_to_track = None
        for ref in origin.refs:
            if ref.name == remote_branch_name_full:
                remote_ref_to_track = ref
                break
        
        if not remote_ref_to_track:
            print(f"Error: Branch '{branch_name}' not found as a local branch, and '{remote_branch_name_full}' not found on remote 'origin'.")
            print("Please fetch changes or check branch name.")
            return False

        # At this point, remote_ref_to_track is valid (e.g., origin.refs['main'] or origin.refs['feature/foo'])
        # Determine local name for the new tracking branch
        local_tracking_branch_name = remote_ref_to_track.remote_head # e.g. 'main' from 'origin/main'

        if local_tracking_branch_name in repo.heads:
            # Local branch with the target name already exists
            local_branch = repo.heads[local_tracking_branch_name]
            if local_branch.tracking_branch() and local_branch.tracking_branch().name == remote_ref_to_track.name:
                print(f"Local branch '{local_tracking_branch_name}' already tracks '{remote_ref_to_track.name}'. Checking it out.")
                local_branch.checkout()
                print(f"Successfully checked out branch: {local_tracking_branch_name}")
                return True
            else:
                print(f"Error: Local branch '{local_tracking_branch_name}' exists but does not track '{remote_ref_to_track.name}'.")
                print("Please resolve this manually (e.g., rename local branch or set tracking).")
                return False
        else:
            # Create new local branch tracking the remote one
            print(f"Creating local branch '{local_tracking_branch_name}' to track remote branch '{remote_ref_to_track.name}'.")
            new_tracking_branch = repo.create_head(local_tracking_branch_name, remote_ref_to_track)
            new_tracking_branch.set_tracking_branch(remote_ref_to_track) # Ensure tracking is set
            new_tracking_branch.checkout()
            print(f"Successfully created and checked out branch '{local_tracking_branch_name}' tracking '{remote_ref_to_track.name}'.")
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
        tracking_branch = current_branch.tracking_branch()

        if not tracking_branch:
            print(f"Error: Current branch '{current_branch.name}' is not tracking any remote branch. Cannot pull.")
            print(f"Please set upstream for '{current_branch.name}' first (e.g., by pushing with --set-upstream or using `git branch --set-upstream-to=origin/{current_branch.name}`).")
            return False
        
        print(f"Pulling changes from '{tracking_branch.remote_name}/{tracking_branch.remote_head}' into local branch '{current_branch.name}'...")
        # origin.pull() pulls the current *tracked* branch by default.
        # We can be more explicit if needed, but this should generally work if tracking is set.
        pull_info = origin.pull()

        if not pull_info:
            print("No pull information returned. This might mean no changes or an issue.")
        else:
            for info in pull_info:
                 print(f"Pulled: {info.name}, Ref: {info.ref}, Summary: {info.summary}, Flags: {info.flags}")
                 if info.flags & info.ERROR:
                     print(f"  Error during pull: {info.ref} - {info.summary}")
                 elif info.flags & info.REJECTED:
                     print(f"  Pull rejected: {info.ref} - {info.summary}")
                 elif info.flags & info.NO_CHANGE:
                     print(f"  No changes for {info.ref}.")
                 elif info.flags & info.FAST_FORWARD or info.flags & info.MERGE:
                     print(f"  Successfully updated {info.ref}.")


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
    parser.add_argument("--repo-name", help="Name of the repository from config to use (will load its local path and GitHub name).")
    parser.add_argument("list_repos", nargs='?', const=True, default=False,
                        help="List all stored repository names and their paths from config and exit.")
    parser.add_argument("--init-repo", action="store_true",
                        help="Initialize a new Git repository in the path specified by --local-path (or prompt if not set).")
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

    local_repo_path_input = None
    github_repo_name_input = None # Will be determined later
    repo_just_created_or_cloned = False

    if args.clone_repo:
        cloned_path = clone_repository(GITHUB_TOKEN)
        if cloned_path:
            local_repo_path_input = cloned_path
            repo_just_created_or_cloned = True
            save_choice = input(f"Repository cloned to '{local_repo_path_input}'. Save to config? (y/n): ").lower()
            if save_choice == 'y':
                config_repo_name = input("Enter a name for this repository in the config: ").strip()
                if config_repo_name:
                    add_repo_to_config(config_repo_name, local_repo_path_input)
                else:
                    print("Invalid name, not saving to config.")
        else:
            print("Cloning failed. Exiting.")
            sys.exit(1)

    if not local_repo_path_input and args.repo_name:
        path_from_config = get_repo_path_from_config(args.repo_name)
        if path_from_config:
            local_repo_path_input = path_from_config
            print(f"Using repository '{args.repo_name}' from config: {local_repo_path_input}")
            # Note: github_repo_name could also be loaded from config here if structure is extended
        else:
            print(f"Error: Repository name '{args.repo_name}' not found in config. Exiting.")
            sys.exit(1)

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
            config_repo_name = input("Enter a name for this new repository in the config: ").strip()
            if config_repo_name:
                add_repo_to_config(config_repo_name, local_repo_path_input)
            else:
                print("Invalid name, not saving to config.")

    # Determine GitHub repository name
    if args.github_repo:
        github_repo_name_input = args.github_repo
        print(f"Using GitHub repo name from command line: {github_repo_name_input}")
    else:
        # Attempt to load from config if --repo-name was used and we extend config for it (future enhancement)
        # For now, just auto-detect or prompt
        print("Attempting to automatically determine GitHub repository name from local git config...")
        github_repo_name_input = get_github_repo_from_local(local_repo_path_input)
        if github_repo_name_input:
            print(f"Auto-detected GitHub repository name: {github_repo_name_input}")
        else:
            print("Could not auto-detect GitHub repository name.")
            github_repo_name_input = input("Enter the GitHub repository name (e.g., username/repo): ").strip()

    if not github_repo_name_input:
        print("Error: GitHub repository name is required for further operations. Exiting.")
        sys.exit(1)

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
        fetch_changes(local_repo_path_input)

    if args.list_branches:
        list_branches(local_repo_path_input) # List branches after potential fetch

    if args.create_branch:
        checkout_branch(local_repo_path_input, args.create_branch, create_new=True)
    elif args.checkout: # Ensure this is mutually exclusive with create_branch if it implies checkout
        checkout_branch(local_repo_path_input, args.checkout)
    
    # Pull operation should ideally be after any checkout or branch creation
    if args.pull:
        pull_changes(local_repo_path_input)
    
    print("\n=== Script completed successfully ===")

if __name__ == "__main__":
    main()
