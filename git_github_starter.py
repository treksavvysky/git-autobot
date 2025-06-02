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
                        repo.index.commit("Initial commit")
                        print("Initial commit created successfully.")
                    except GitCommandError as commit_error:
                        print(f"Error creating initial commit: {commit_error}")
                        # Still return True as repo was initialized
                    except Exception as e_commit:
                        print(f"An unexpected error occurred during initial commit: {e_commit}")
                        # Still return True as repo was initialized
                else:
                    print("Skipping initial commit.")
                return True
            except GitCommandError as init_error:
                print(f"Error initializing repository: {init_error}")
                return False
            except Exception as e_init:
                print(f"An unexpected error occurred during repository initialization: {e_init}")
                return False
        else:
            print("Repository initialization skipped by user.")
            return False
    except Exception as e:
        print(f"An unexpected error occurred while checking/initializing local repository: {e}")
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

    if not github_repo_exists(GITHUB_TOKEN, github_repo_name_input):
        print(f"Error: GitHub repository '{github_repo_name_input}' not found or not accessible. Exiting.")
        sys.exit(1)
    
    print(f"\nProceeding with operations for local repo: '{local_repo_path_input}' and GitHub repo: '{github_repo_name_input}'\n")

    # --- Local Git Operations ---
    print("1. Checking local Git repository status...")
    changes_made = check_git_status_and_commit(local_repo_path_input)
    print()
    
    # --- GitHub API Operations ---
    if GITHUB_TOKEN:
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
    else:
        print("Skipping GitHub API operations (GITHUB_TOKEN not set).")
    
    print("\n=== Script completed successfully ===")

if __name__ == "__main__":
    main()
