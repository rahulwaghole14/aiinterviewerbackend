#!/bin/bash

# AI Interviewer Deployment Script for Render
# This script helps automate the deployment process

echo "🚀 AI Interviewer Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository. Please initialize git first."
    exit 1
fi

print_status "Checking repository status..."

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_warning "You have uncommitted changes. Please commit them before deploying."
    echo "Current changes:"
    git status --porcelain
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled."
        exit 1
    fi
fi

print_status "Preparing for deployment..."

# Create production environment file for frontend
print_status "Creating production environment file for frontend..."
cat > frontend/.env.production << EOF
# Production Environment Variables for Frontend
VITE_API_URL=https://ai-interviewer-backend.onrender.com
VITE_APP_NAME=AI Interviewer
VITE_APP_VERSION=1.0.0
EOF

print_status "Production environment file created: frontend/.env.production"

# Check if render.yaml exists and is properly configured
if [ ! -f "render.yaml" ]; then
    print_error "render.yaml file not found. Please create it first."
    exit 1
fi

print_status "render.yaml found. Checking configuration..."

# Validate render.yaml structure
if ! grep -q "ai-interviewer-backend" render.yaml; then
    print_error "Backend service not found in render.yaml"
    exit 1
fi

if ! grep -q "ai-interviewer-frontend" render.yaml; then
    print_error "Frontend service not found in render.yaml"
    exit 1
fi

print_status "render.yaml configuration looks good!"

# Check requirements.txt
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in root directory"
    exit 1
fi

# Check frontend package.json
if [ ! -f "frontend/package.json" ]; then
    print_error "frontend/package.json not found"
    exit 1
fi

print_status "All required files found."

# Check if we have a remote repository
if ! git remote get-url origin &> /dev/null; then
    print_warning "No remote repository found. You'll need to add one:"
    echo "git remote add origin <your-github-repo-url>"
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled."
        exit 1
    fi
fi

# Commit the production environment file
print_status "Committing production environment file..."
git add frontend/.env.production
git commit -m "Add production environment configuration" || {
    print_warning "No changes to commit or commit failed"
}

# Push to remote repository
print_status "Pushing to remote repository..."
if git push origin main; then
    print_status "Code pushed successfully!"
else
    print_error "Failed to push to remote repository"
    exit 1
fi

echo
echo "🎉 Deployment Preparation Complete!"
echo "=================================="
echo
echo "Next steps:"
echo "1. Go to https://dashboard.render.com"
echo "2. Create a new Web Service for the backend"
echo "3. Create a new Static Site for the frontend"
echo "4. Connect your GitHub repository"
echo "5. Configure environment variables"
echo
echo "Backend Environment Variables:"
echo "- SECRET_KEY: Generate a secure key"
echo "- DEBUG: false"
echo "- ALLOWED_HOSTS: .onrender.com"
echo "- CORS_ALLOWED_ORIGINS: https://your-frontend-app.onrender.com"
echo "- DATABASE_URL: Will be provided by Render"
echo
echo "Frontend Environment Variables:"
echo "- VITE_API_URL: https://your-backend-app.onrender.com"
echo
echo "For detailed instructions, see: RENDER_DEPLOYMENT_GUIDE.md"
echo
print_status "Deployment script completed successfully!"

