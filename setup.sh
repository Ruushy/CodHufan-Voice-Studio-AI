#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Voice Studio AI — Quick Setup Script
# Usage: bash setup.sh
# ══════════════════════════════════════════════════════════════════
set -e

echo ""
echo "╔════════════════════════════════════╗"
echo "║   Codhufan Voice Studio AI — Setup          ║"
echo "╚════════════════════════════════════╝"
echo ""

# Check Python
python_version=$(python3 --version 2>&1 || echo "NOT FOUND")
echo "Python: $python_version"

# Check FFmpeg
ffmpeg_version=$(ffmpeg -version 2>&1 | head -1 || echo "NOT FOUND")
echo "FFmpeg: $ffmpeg_version"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required. Please install Python 3.10+."
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "WARNING: FFmpeg not found on PATH."
    echo "  macOS:  brew install ffmpeg"
    echo "  Ubuntu: sudo apt install ffmpeg"
    echo "  Windows: https://ffmpeg.org/download.html"
    echo ""
fi

# Create virtualenv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing PyTorch (CPU version)..."
echo "If you have a CUDA GPU, run instead:"
echo "  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121"
echo ""
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu -q

echo ""
echo "Installing project dependencies..."
pip install -r requirements.txt -q

echo ""
echo "Running Django migrations..."
python manage.py migrate

echo ""
echo "Creating media directories..."
mkdir -p media/uploads media/processed

echo ""
echo "╔════════════════════════════════════╗"
echo "║   Setup Complete!                  ║"
echo "╚════════════════════════════════════╝"
echo ""
echo "Start the server with:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Then open: http://127.0.0.1:8000"
echo ""
