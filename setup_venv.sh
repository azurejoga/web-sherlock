#!/bin/bash
# Web Sherlock - Virtual Environment Setup Script for Linux/macOS
# This script creates and configures a Python virtual environment

set -e

echo "🔧 Web Sherlock - Virtual Environment Setup"
echo "=========================================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. You have $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt


echo ""
echo "🎉 Setup Complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "    source venv/bin/activate"
echo ""
echo "To start Web Sherlock, run:"
echo "    python main.py"
echo ""
echo "To deactivate the virtual environment, run:"
echo "    deactivate"