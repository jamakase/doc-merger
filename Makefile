w.PHONY: help install dev dev-backend dev-frontend stop build clean test
.PHONY: help install dev dev-backend dev-frontend stop build clean test

# Default target
help:
	@echo "🚀 Document Extractor - Development Commands"
	@echo "════════════════════════════════════════════"
	@echo "📦 install        - Install all dependencies"
	@echo "🔥 dev            - Run both backend and frontend in dev mode"
	@echo "🐍 dev-backend    - Run only Python FastAPI backend"
	@echo "🌐 dev-frontend   - Run only Next.js frontend"
	@echo "🛑 stop           - Stop all running services"
	@echo "🏗️  build          - Build frontend for production"
	@echo "🧹 clean          - Clean temporary files and dependencies"
	@echo "🧪 test           - Run tests"
	@echo "✅ check          - Check system requirements"

# Install all dependencies
install:
	@echo "📦 Creating and activating virtual environment..."
	python -m venv .venv
	. .venv/bin/activate
	@echo "📦 Installing Python dependencies..."
	uv sync
	@echo "📦 Installing Node.js dependencies..."
	cd my-app && npm install
	@echo "✅ All dependencies installed!"

# Main development command - runs both services
dev:
	@echo "🚀 Starting Document Extractor in development mode..."
	@echo "🐍 Backend will run on: http://localhost:8000"
	@echo "🌐 Frontend will run on: http://localhost:3000"
	@echo "📊 API docs available at: http://localhost:8000/docs"
	@echo ""
	@echo "Press Ctrl+C to stop all services"
	@echo "════════════════════════════════════════════"
	@make -j2 dev-backend dev-frontend

# Run backend only
dev-backend:
	@echo "🐍 Starting FastAPI backend..."
	. .venv/bin/activate && python start_api.py

# Run frontend only  
dev-frontend:
	@echo "🌐 Starting Next.js frontend..."
	cd my-app && npm run dev

# Stop all services (kill processes on ports 3000 and 8000)
stop:
	@echo "🛑 Stopping all services..."
	-pkill -f "python start_api.py" 2>/dev/null || true
	-pkill -f "next dev" 2>/dev/null || true
	-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@echo "✅ All services stopped"

# Build frontend for production
build:
	@echo "🏗️ Building frontend for production..."
	cd my-app && npm run build
	@echo "✅ Build complete!"

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	rm -rf extracted_documents_*
	rm -rf temp_downloads
	rm -rf my-app/.next
	rm -rf my-app/node_modules/.cache
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .venv
	@echo "✅ Cleanup complete!"

# Run tests
test:
	@echo "🧪 Running tests..."
	@echo "⚠️  Tests not implemented yet"

# Check system requirements
check:
	@echo "✅ Checking system requirements..."
	@python --version
	@node --version
	@npm --version
	@echo "🔍 Checking Python packages..."
	@. .venv/bin/activate && uv pip list | grep -E "(fastapi|uvicorn|pydantic)" || echo "⚠️  Some Python packages missing"
	@echo "🔍 Checking Node.js packages..."
	@cd my-app && npm list next react 2>/dev/null | grep -E "(next|react)" || echo "⚠️  Some Node.js packages missing"
	@echo "✅ System check complete!"

# Development shortcuts
start: dev
server: dev-backend
client: dev-frontend
frontend: dev-frontend
backend: dev-backend
api: dev-backend