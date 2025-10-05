#!/bin/bash

# Zero-downtime deployment script for borrzu
# This script builds new images first, then does a quick swap to minimize downtime

set -e  # Exit on any error

echo "🚀 Starting zero-downtime deployment to borrzu..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to run commands on remote server
run_remote() {
    ssh borrzu "cd project/0xpads_listener && $1"
}

print_status "Step 1: Pulling latest code..."
run_remote "git pull"

print_status "Step 2: Building new Docker images (this may take a few minutes)..."
run_remote "docker compose build"

print_status "Step 3: Creating new containers with updated images..."
run_remote "docker compose up -d --no-deps"

print_status "Step 4: Waiting for new containers to be ready..."
sleep 10

print_status "Step 5: Checking container health..."
if run_remote "docker compose ps | grep -q 'Up'"; then
    print_success "New containers are running successfully!"
else
    print_error "New containers failed to start properly!"
    print_warning "Rolling back to previous version..."
    run_remote "docker compose down && docker compose up -d"
    exit 1
fi

print_status "Step 6: Cleaning up old unused images..."
run_remote "docker image prune -f"

print_success "🎉 Zero-downtime deployment completed successfully!"
print_status "Application is now running with the latest code."

# Optional: Show running containers
print_status "Current running containers:"
run_remote "docker compose ps"