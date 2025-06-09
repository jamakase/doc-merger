#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Document Extractor System${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping services...${NC}"
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Check if Python virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not detected. Consider running:${NC}"
    echo -e "${YELLOW}   source .venv/bin/activate${NC}"
    echo ""
fi

# Start API server
echo -e "${GREEN}🔧 Starting FastAPI server...${NC}"
python start_api.py &
API_PID=$!

# Wait for API server to start
echo -e "${YELLOW}⏳ Waiting for API server to initialize...${NC}"
sleep 5

# Check if API server is running
if kill -0 $API_PID 2>/dev/null; then
    echo -e "${GREEN}✅ API server started successfully (PID: $API_PID)${NC}"
else
    echo -e "${RED}❌ Failed to start API server${NC}"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "my-app/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
    cd my-app && npm install && cd ..
fi

# Start frontend
echo -e "${GREEN}🌐 Starting Next.js frontend...${NC}"
cd my-app
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 3

# Check if frontend is running
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Frontend started successfully (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ Failed to start frontend${NC}"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 System is ready!${NC}"
echo ""
echo -e "${GREEN}📊 API Server:${NC}     http://localhost:8000"
echo -e "${GREEN}📊 API Docs:${NC}       http://localhost:8000/docs"
echo -e "${GREEN}🌐 Frontend:${NC}       http://localhost:3000"
echo ""
echo -e "${YELLOW}💡 Press Ctrl+C to stop all services${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"

# Wait for user interrupt
wait 