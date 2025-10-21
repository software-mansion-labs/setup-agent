#!/bin/bash
set -e

if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing..."

    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "uv is already installed: $(uv --version)"
fi

uv sync
uv build