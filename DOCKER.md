# Docker Setup for Git Autobot

This guide explains how to run the Git Autobot application using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- GitHub Personal Access Token

## Quick Start

### 1. Set up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit the file and add your GitHub token
nano .env
```

Add your GitHub Personal Access Token:

```env
GITHUB_TOKEN=your_github_token_here
```

### 2. Run with Docker Compose

#### Development Mode (with hot reload)

```bash
# Build and start both services
docker-compose -f docker-compose.dev.yml up --build

# Or run in background
docker-compose -f docker-compose.dev.yml up --build -d
```

#### Production Mode

```bash
# Build and start both services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Docker Compose Files

### `docker-compose.yml` (Production)
- Optimized builds for production
- Standalone Next.js output
- Non-root user for security

### `docker-compose.dev.yml` (Development)
- Hot reload for both frontend and backend
- Volume mounts for live code changes
- Development-friendly configuration

## Services

### Backend Service
- **Image**: Built from `Dockerfile`
- **Port**: 8000
- **Environment**: 
  - `GITHUB_TOKEN`: Your GitHub Personal Access Token
- **Features**:
  - FastAPI with CORS enabled
  - Auto-reload in development mode
  - Non-root user for security

### Frontend Service
- **Image**: Built from `frontend/Dockerfile`
- **Port**: 3000
- **Environment**:
  - `NEXT_PUBLIC_API_URL`: Backend API URL
- **Features**:
  - Next.js 15 with TypeScript
  - Tailwind CSS
  - Hot reload in development mode

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Required |
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `BACKEND_HOST` | Backend host | `0.0.0.0` |
| `BACKEND_PORT` | Backend port | `8000` |

## Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Rebuild Services
```bash
# Rebuild without cache
docker-compose build --no-cache

# Rebuild specific service
docker-compose build backend
```

### Access Container Shell
```bash
# Backend container
docker-compose exec backend bash

# Frontend container
docker-compose exec frontend sh
```

## Troubleshooting

### GitHub Token Issues
- Make sure your `.env` file contains a valid GitHub token
- Verify the token has the necessary permissions (repo access)
- Check the backend logs for authentication errors

### Port Conflicts
- Ensure ports 3000 and 8000 are not in use by other applications
- Modify the port mappings in `docker-compose.yml` if needed

### Build Issues
- Clear Docker cache: `docker system prune -a`
- Rebuild without cache: `docker-compose build --no-cache`

### Network Issues
- Services communicate via the `git-autobot-network`
- Frontend uses `http://backend:8000` to reach the backend internally
- External access uses `http://localhost:8000`

## Development Workflow

1. **Start development environment**:
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Make code changes** - Both frontend and backend will auto-reload

3. **View logs**:
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f
   ```

4. **Stop when done**:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

## Production Deployment

For production deployment:

1. Set up proper environment variables
2. Use production Docker Compose file
3. Consider using a reverse proxy (nginx)
4. Set up proper logging and monitoring
5. Use Docker secrets for sensitive data

```bash
# Production deployment
docker-compose up --build -d
```
