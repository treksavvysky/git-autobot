# Git Autobot

A Python toolkit for automating Git and GitHub operations using GitPython and PyGithub.

## Installation

```bash
pip install GitPython PyGithub
```

## Setup

1. **GitHub Token**: Create a personal access token on GitHub and set it as an environment variable:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```

2. **Configuration**: Edit the configuration variables in `git_github_starter.py`:
   - `LOCAL_REPO_PATH`: Path to your local Git repository
   - `GITHUB_REPO_NAME`: Your GitHub repository in format "username/repo"

## Usage

Run the starter script:
```bash
python git_github_starter.py
```

## Features

The starter script demonstrates:
- **Local Git Operations**:
  - Check repository status
  - Add and commit changes
  - Push to remote repository
  
- **GitHub API Operations**:
  - Get repository information
  - Create issues with labels
  - Handle authentication and errors

## Example Workflow

1. Script checks for uncommitted changes in your local repo
2. If changes exist, it commits and pushes them
3. Retrieves repository information from GitHub
4. Creates a GitHub issue documenting the automated update

## Security Notes

- Never commit your GitHub token to version control
- Use environment variables or secure credential storage
- Consider using GitHub Apps for production automation

## Extending the Script

You can easily extend this starter code to:
- Create pull requests
- Manage repository settings
- Automate release workflows
- Sync multiple repositories
- Generate reports from commit history
