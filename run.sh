#!/usr/bin/env bash
set -e

echo "======================================================="
echo "  SPCIS - Self-Playing Cyber Immune System"
echo "  Launching Cyber Defense Command Center..."
echo "======================================================="

# Activate virtual environment if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting SPCIS API Server and Web UI on http://127.0.0.1:8000 ..."

# Attempt to open browser across OS
if which xdg-open > /dev/null; then
  xdg-open http://127.0.0.1:8000 &
elif which open > /dev/null; then
  open http://127.0.0.1:8000 &
fi

python3 server.py --host 127.0.0.1 --port 8000
