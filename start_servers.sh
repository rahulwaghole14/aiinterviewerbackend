#!/bin/bash

# Combined Server Starter for AI Interview Platform (Unix/Linux/macOS)
# Starts both Django backend and React frontend servers simultaneously

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_DIR="$SCRIPT_DIR/venv"

echo -e "${BLUE}🎯 AI Interview Platform - Combined Server Starter${NC}"
echo "=================================================="

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping servers...${NC}"
    
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Stopping backend server (PID: $BACKEND_PID)${NC}"
        kill -TERM $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Stopping frontend server (PID: $FRONTEND_PID)${NC}"
        kill -TERM $FRONTEND_PID 2>/dev/null || true
        wait $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}🎉 All servers stopped successfully${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM EXIT

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_DIR${NC}"
    echo -e "${YELLOW}💡 Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

# Check if node_modules exists, install if not
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd "$FRONTEND_DIR"
    npm install
    cd "$SCRIPT_DIR"
fi

echo -e "${GREEN}✅ All prerequisites met!${NC}"

# Start backend server
echo -e "${BLUE}🚀 Starting Django backend server...${NC}"
cd "$SCRIPT_DIR"
source "$VENV_DIR/bin/activate"

# Start backend in background
python manage.py runserver 127.0.0.1:8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Check if backend started successfully
sleep 3
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start backend server${NC}"
    echo -e "${YELLOW}📋 Check backend.log for details${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend server started on http://127.0.0.1:8000 (PID: $BACKEND_PID)${NC}"

# Start frontend server
echo -e "${BLUE}🚀 Starting React frontend server...${NC}"
cd "$FRONTEND_DIR"

# Start frontend in background
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Check if frontend started successfully
sleep 3
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start frontend server${NC}"
    echo -e "${YELLOW}📋 Check frontend.log for details${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend server started on http://localhost:5173 (PID: $FRONTEND_PID)${NC}"

# Success message
echo ""
echo -e "${GREEN}🎉 Both servers are running!${NC}"
echo -e "${BLUE}📍 Backend:  http://127.0.0.1:8000${NC}"
echo -e "${BLUE}📍 Frontend: http://localhost:5173${NC}"
echo ""
echo -e "${YELLOW}💡 Press Ctrl+C to stop both servers${NC}"
echo -e "${YELLOW}📋 Logs: backend.log, frontend.log${NC}"
echo ""

# Keep script running and monitor processes
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend process died${NC}"
        break
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend process died${NC}"
        break
    fi
    
    sleep 1
done

# If we get here, one of the processes died
echo -e "${YELLOW}⚠️  One or more servers stopped unexpectedly${NC}"
cleanup
