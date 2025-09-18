#!/bin/bash

# Git Autobot Docker Runner Script
# This script helps you run the Git Autobot application using Docker Compose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_REPO_PATH=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

resolve_repo_path() {
    local chosen_path=""

    if [ -n "$CLI_REPO_PATH" ]; then
        chosen_path="$CLI_REPO_PATH"
    elif [ -n "${REPO_PATH:-}" ]; then
        chosen_path="$REPO_PATH"
    else
        if [ -f ".env" ]; then
            local env_line
            env_line=$(grep -E '^REPO_PATH=' .env | tail -n1)
            if [ -n "$env_line" ]; then
                chosen_path=${env_line#REPO_PATH=}
                chosen_path=${chosen_path%"}
                chosen_path=${chosen_path#"}
            fi
        fi
        if [ -z "$chosen_path" ]; then
            chosen_path="$SCRIPT_DIR/local_repos"
        fi
    fi

    if [[ "$chosen_path" == ~* ]]; then
        chosen_path="${chosen_path/#\~/$HOME}"
    fi
    if [[ "$chosen_path" != /* ]]; then
        chosen_path="$(pwd)/$chosen_path"
    fi

    mkdir -p "$chosen_path"
    if ! chosen_path=$(cd "$chosen_path" && pwd); then
        print_error "Unable to resolve repository path: $chosen_path"
        exit 1
    fi

    export REPO_PATH="$chosen_path"
    print_status "Using repository path: $REPO_PATH"
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success ".env file created from .env.example"
            print_warning "Please edit .env file and add your GitHub token:"
            print_warning "  GITHUB_TOKEN=your_github_token_here"
            return 1
        else
            print_error ".env.example file not found. Please create .env file manually."
            return 1
        fi
    fi
    
    # Check if GITHUB_TOKEN is set
    if ! grep -q "GITHUB_TOKEN=.*[^[:space:]]" .env; then
        print_warning "GITHUB_TOKEN is not set in .env file"
        print_warning "Please edit .env file and add your GitHub token:"
        print_warning "  GITHUB_TOKEN=your_github_token_here"
        return 1
    fi
    
    return 0
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [--repo-path /absolute/path] COMMAND"
    echo ""
    echo "Commands:"
    echo "  dev     Start development environment (with hot reload)"
    echo "  prod    Start production environment"
    echo "  stop    Stop all services"
    echo "  logs    Show logs for all services"
    echo "  build   Build Docker images"
    echo "  clean   Stop services and remove containers/volumes"
    echo "  help    Show this help message"
    echo ""
    echo "Options:"
    echo "  --repo-path PATH   Override the host directory for local repository clones"
    echo ""
    echo "Examples:"
    echo "  $0 --repo-path /work/repos dev   # Start dev mode with custom clone path"
    echo "  $0 prod                            # Start production environment"
    echo "  $0 logs                            # View logs"
    echo "  $0 stop                            # Stop all services"
}

# Function to start development environment
start_dev() {
    print_status "Starting development environment..."

    if ! check_env_file; then
        exit 1
    fi

    resolve_repo_path
    docker compose -f docker-compose.dev.yml up --build
}

# Function to start production environment
start_prod() {
    print_status "Starting production environment..."
    
    if ! check_env_file; then
        exit 1
    fi

    resolve_repo_path
    docker compose up --build
}

# Function to stop services
stop_services() {
    print_status "Stopping all services..."
    resolve_repo_path
    docker compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker compose down 2>/dev/null || true
    print_success "All services stopped"
}

# Function to show logs
show_logs() {
    print_status "Showing logs for all services..."
    resolve_repo_path
    docker compose -f docker-compose.dev.yml logs -f 2>/dev/null || docker compose logs -f
}

# Function to build images
build_images() {
    print_status "Building Docker images..."
    resolve_repo_path
    docker compose -f docker-compose.dev.yml build
    print_success "Images built successfully"
}

# Function to clean up
clean_up() {
    print_status "Cleaning up Docker resources..."
    resolve_repo_path
    docker compose -f docker-compose.dev.yml down -v 2>/dev/null || true
    docker compose down -v 2>/dev/null || true
    docker system prune -f
    print_success "Cleanup completed"
}

# Parse global options
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo-path)
            CLI_REPO_PATH="$2"
            shift 2
            ;;
        --repo-path=*)
            CLI_REPO_PATH="${1#*=}"
            shift 1
            ;;
        -r)
            CLI_REPO_PATH="$2"
            shift 2
            ;;
        *)
            ARGS+=("$1")
            shift 1
            ;;
    esac
done

set -- "${ARGS[@]}"

# Main script logic
case "${1:-help}" in
    "dev")
        start_dev
        ;;
    "prod")
        start_prod
        ;;
    "stop")
        stop_services
        ;;
    "logs")
        show_logs
        ;;
    "build")
        build_images
        ;;
    "clean")
        clean_up
        ;;
    "help"|*)
        show_usage
        ;;
esac
