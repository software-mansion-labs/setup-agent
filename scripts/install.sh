#!/bin/bash
set -e

latest_whl=$(ls -t dist/*.whl 2>/dev/null | head -n 1)

if [ -z "$latest_whl" ]; then
  echo "No .whl file found in dist/. Running build.sh..."
  ./scripts/build.sh
  latest_whl=$(ls -t dist/*.whl 2>/dev/null | head -n 1)
  
  if [ -z "$latest_whl" ]; then
    echo "Build failed: no .whl file generated."
    exit 1
  fi
fi

echo "Installing $latest_whl ..."
pip3 install "$latest_whl"

echo "Setup complete. You can now use your CLI."
