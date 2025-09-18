#!/bin/bash

# Git Autobot Development Startup Script
# This script starts both the FastAPI backend and Next.js frontend

echo "🚀 Starting Git Autobot Development Environment"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "fastapi_app.py" ]; then
    echo "❌ Error: fastapi_app.py not found. Please run this script from the git-autobot root directory."
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found. Please make sure the Next.js app is created."
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "📦 Starting FastAPI backend on http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo ""

# Start FastAPI backend
python -m uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo "🌐 Starting Next.js frontend on http://localhost:3000"
echo ""

# Start Next.js frontend
cd frontend
npm run dev &
FRONTEND_PID=$!

# Go back to root directory
cd ..

echo "✅ Development environment is running!"
echo ""
echo "🔗 URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait
