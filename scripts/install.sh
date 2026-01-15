#!/bin/bash
set -e

REQUIRED_PYTHON="3.13.0"

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

install_python_with_pyenv() {
    if ! command -v pyenv >/dev/null 2>&1; then
        if [ -d "$HOME/.pyenv" ]; then
            echo "pyenv directory found at $HOME/.pyenv — reusing existing installation."
        else
            echo "pyenv not found. Installing pyenv..."
            curl https://pyenv.run | bash
        fi
    else
        echo "pyenv command found — reusing existing installation."
    fi

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)" 2>/dev/null || true

    if ! pyenv versions --bare | grep -q "^${REQUIRED_PYTHON}$"; then
        echo "Installing Python $REQUIRED_PYTHON with pyenv..."
        pyenv install -s "$REQUIRED_PYTHON"
    else
        echo "Python $REQUIRED_PYTHON already installed."
    fi

    pyenv shell "$REQUIRED_PYTHON"
    echo "Using Python $(python3 --version)"
}

if command -v brew >/dev/null 2>&1; then
    echo "Installing pipx using Homebrew..."
    brew install pipx
else
    echo "Homebrew not found. Installing required Python and pipx..."
    install_python_with_pyenv

    python3 -m ensurepip --upgrade
    python3 -m pip install --user --upgrade pip pipx
fi

export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/Library/Python/$(python3 -c 'import sys; print(sys.version[:3])')/bin:$PATH"

echo "Installing $latest_whl ..."
pipx install --force "$latest_whl"

PIPX_BIN_DIR=$(python3 -m pipx environment 2>/dev/null | grep 'apps are exposed on your \$PATH at' | awk '{print $NF}')
if [ -z "$PIPX_BIN_DIR" ]; then
  PIPX_BIN_DIR="$HOME/.local/bin"
fi

if [ -n "$ZDOTDIR" ]; then
  ZSHRC_FILE="$ZDOTDIR/.zshrc"
else
  ZSHRC_FILE="$HOME/.zshrc"
fi

if ! grep -q "$PIPX_BIN_DIR" "$ZSHRC_FILE" 2>/dev/null; then
  echo "" >> "$ZSHRC_FILE"
  echo "# Added by setup-agent installer on $(date)" >> "$ZSHRC_FILE"
  echo "export PATH=\"$PIPX_BIN_DIR:\$PATH\"" >> "$ZSHRC_FILE"
  echo "✅ Added $PIPX_BIN_DIR to PATH in $ZSHRC_FILE"
else
  echo "ℹ️ PATH entry for $PIPX_BIN_DIR already exists in $ZSHRC_FILE"
fi

export PATH="$PIPX_BIN_DIR:$PATH"

echo ""
echo "Verifying installation..."
if command -v setup-agent >/dev/null 2>&1; then
    echo "✅ setup-agent is now available on your PATH!"
else
    echo "⚠️ setup-agent not found automatically."
    echo "Run this to fix it:"
    echo "    export PATH=\"$PIPX_BIN_DIR:\$PATH\""
    echo "Then restart your terminal or run: source $ZSHRC_FILE"
fi

echo ""
echo "Setup complete!"
echo "You can now run: setup-agent --help"
