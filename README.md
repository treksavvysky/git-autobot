# Git Autobot

A powerful developer CLI tool to streamline git workflows and repository management.

## Features

### 🏗️ **Modular Architecture**

- **Repository Management**: Add, remove, list, and configure multiple repositories
- **Git Operations**: Comprehensive git workflow automation
- **Rich CLI**: Beautiful, interactive command-line interface with help and completion
- **Flexible Targeting**: Work with repositories via aliases, paths, or current directory

### 🗂️ **Repository Management**

- Store and manage multiple repository configurations
- Auto-detect GitHub repository information
- Track important branches per repository
- Rich tabular display of repository information

### 🔄 **Git Operations**

- Repository status with beautiful formatting
- Branch management and visualization
- Commit, push, pull operations
- Quick-commit for rapid development
- Repository synchronization (commit + pull + push)

## Installation

Install the package in editable mode:

```bash
uv pip install -e .
```

## Quick Start

### 1. Add a Repository

```bash
# Add current directory
git-autobot repo add my-project . --desc "My awesome project"

# Add with GitHub info
git-autobot repo add my-api /path/to/api --github user/api-repo --branches "main,develop"
```

### 2. List Repositories

```bash
git-autobot repo list
```

### 3. Git Operations

```bash
# Check status of current repo
git-autobot git status

# Check status using alias
git-autobot git status --alias my-project

# Quick commit and stage
git-autobot git quick-commit "Fix important bug"

# Sync repository (commit + pull + push)
git-autobot git sync --message "Update from local changes"
```

## Commands Reference

### Repository Management (`git-autobot repo`)

| Command              | Description                          |
| -------------------- | ------------------------------------ |
| `add <alias> <path>` | Add repository to configuration      |
| `remove <alias>`     | Remove repository from configuration |
| `list`               | List all configured repositories     |
| `show <alias>`       | Show detailed repository information |
| `update <alias>`     | Update repository configuration      |

**Add Command Options:**

- `--github, -g`: GitHub repository name (user/repo)
- `--branches, -b`: Important branches (comma-separated)
- `--url, -u`: Git remote URL
- `--desc, -d`: Repository description

### Git Operations (`git-autobot git`)

| Command                  | Description                                 |
| ------------------------ | ------------------------------------------- |
| `status`                 | Show repository status with rich formatting |
| `branches`               | Display branch information                  |
| `add`                    | Stage all changes                           |
| `commit <message>`       | Commit with message                         |
| `push`                   | Push to remote                              |
| `pull`                   | Pull from remote                            |
| `checkout <branch>`      | Checkout branch                             |
| `quick-commit <message>` | Stage all + commit + optional push          |
| `sync`                   | Full sync: commit local changes, pull, push |

**Targeting Options (available for all git commands):**

- `--alias, -a`: Use configured repository alias
- `--path, -p`: Use direct repository path
- _(no option)_: Use current directory if it's a git repository

**Additional Options:**

- `commit --add`: Stage all changes before committing
- `checkout --create, -c`: Create branch if it doesn't exist
- `quick-commit --push`: Push after committing
- `sync --message, -m`: Custom commit message for local changes

## Examples

### Setting Up Multiple Projects

```bash
# Add your main projects
git-autobot repo add frontend ~/projects/my-app-frontend --github myorg/frontend
git-autobot repo add backend ~/projects/my-app-backend --github myorg/backend --branches "main,develop,staging"
git-autobot repo add scripts ~/scripts --desc "Utility scripts"

# View all projects
git-autobot repo list
```

### Daily Workflow

```bash
# Check status of all your projects
git-autobot git status --alias frontend
git-autobot git status --alias backend

# Quick development cycle
cd ~/projects/my-app-frontend
git-autobot git quick-commit "Add new feature"
git-autobot git sync  # Commit any remaining changes, pull, and push

# Work with branches
git-autobot git checkout develop --alias backend
git-autobot git branches --alias backend
```

### Repository Management

```bash
# Update repository info
git-autobot repo update frontend --branches "main,develop,feature/new-ui"

# Show detailed info
git-autobot repo show backend

# Remove old projects
git-autobot repo remove old-project --force
```

## Configuration

Repository configurations are stored in `repo_config.json` in the current directory. The configuration includes:

```json
{
  "my-project": {
    "path": "/absolute/path/to/repository",
    "github_repo_name": "user/repository",
    "branches": ["main", "develop"],
    "url": "git@github.com:user/repository.git",
    "description": "Project description"
  }
}
```

## Development

### Architecture

The project follows a modular architecture:

```
git_autobot/
├── __main__.py          # Main CLI entry point
├── core/                # Core functionality
│   ├── config.py        # Configuration management
│   └── git_ops.py       # Git operations
└── commands/            # Command modules
    ├── repo.py          # Repository management commands
    └── git_ops.py       # Git operation commands
```

### Key Design Principles

1. **Modularity**: Each command group is in its own module
2. **Rich UI**: Beautiful tables and formatting using Rich library
3. **Flexible Targeting**: Multiple ways to specify repositories
4. **Error Handling**: Graceful error handling with helpful messages
5. **Extensibility**: Easy to add new command groups and operations

### Adding New Commands

To add a new command group:

1. Create a new module in `commands/`
2. Define a Typer app for the command group
3. Add commands to the app
4. Import and add to main CLI in `__main__.py`

## Version

Current version: **0.2.0**

## Requirements

- Python >= 3.13
- GitPython >= 3.1.44
- PyGithub >= 2.6.1
- Typer >= 0.12.3
- Rich >= 13.0.0
- python-dotenv >= 1.0.0

## Web Interface

Git Autobot now includes a modern web interface built with Next.js and FastAPI.

### Architecture

- **Backend**: FastAPI server (`fastapi_app.py`) providing GitHub repository API
- **Frontend**: Next.js 15 application with TypeScript and Tailwind CSS
- **Features**: Modern UI, responsive design, GitHub token authentication

### Quick Start

#### Option 1: Docker Compose (Recommended)

1. **Set up environment variables**:

   ```bash
   cp .env.example .env
   # Edit .env and add your GitHub token
   nano .env
   ```

2. **Start with Docker Compose**:

   ```bash
   # Development mode (with hot reload)
   ./docker-run.sh dev

   # Or production mode
   ./docker-run.sh prod
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

#### Option 2: Local Development

1. **Start both servers** (recommended):

   ```bash
   ./start-dev.sh
   ```

   This will start both the FastAPI backend and Next.js frontend.

2. **Or start individually**:

   **Backend**:

   ```bash
   uv run uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
   ```

   **Frontend**:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Frontend Features

- 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS
- 🔐 **Authentication**: Secure GitHub token input
- 📱 **Mobile-First**: Responsive design for all devices
- ⚡ **Fast**: Built with Next.js 15 and Turbopack
- 🛡️ **Type-Safe**: Full TypeScript support

### Environment Setup

Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Docker Deployment

#### Using Docker Compose (Recommended)

The easiest way to run the entire application is using Docker Compose:

```bash
# Set up environment
cp .env.example .env
# Edit .env and add your GitHub token

# Development mode
./docker-run.sh dev

# Production mode
./docker-run.sh prod
```

#### Manual Docker Deployment

1. Build the backend image:
   ```bash
   docker build -t git-autobot-api .
   ```
2. Run the container:
   ```bash
   docker run -e GITHUB_TOKEN=your_token -p 8000:8000 git-autobot-api
   ```
3. Deploy the frontend to Vercel, Netlify, or your preferred platform.

#### Docker Commands

```bash
# Start development environment
./docker-run.sh dev

# Start production environment
./docker-run.sh prod

# View logs
./docker-run.sh logs

# Stop services
./docker-run.sh stop

# Clean up
./docker-run.sh clean
```

For detailed Docker setup instructions, see [DOCKER.md](DOCKER.md).

### API Endpoints

- `GET /repos` - List user repositories
  - Query parameter: `token` (optional GitHub Personal Access Token)
  - Returns: Array of repository objects with name, full_name, and html_url
