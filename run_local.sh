#!/bin/bash
# Web Sherlock - Local Development Server Script
# Quick start script for development

set -e

echo "🚀 Starting Web Sherlock Local Development Server"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup_venv.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Set environment variables for development
export FLASK_ENV=development
export FLASK_DEBUG=1
export SESSION_SECRET=${SESSION_SECRET:-"dev-secret-key-change-in-production"}

# Check if required directories exist
mkdir -p uploads results history translations static/css static/js templates

echo "✅ Environment ready"
echo "🌐 Starting Flask development server on http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python main.py