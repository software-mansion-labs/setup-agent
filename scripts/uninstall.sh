#!/bin/bash
set -e

APP_NAME="setup-agent"

echo "🔧 Uninstalling $APP_NAME ..."

if command -v pipx >/dev/null 2>&1; then
    if pipx list | grep -q "$APP_NAME"; then
        echo "Removing $APP_NAME using pipx..."
        pipx uninstall "$APP_NAME"
    else
        echo "ℹ️ $APP_NAME is not currently installed via pipx."
    fi
else
    echo "⚠️ pipx not found — skipping pipx uninstall."
fi

POSSIBLE_DIRS=(
    "$HOME/.local/bin"
    "$HOME/Library/Python/$(python3 -c 'import sys; print(sys.version[:3])' 2>/dev/null)/bin"
)

for dir in "${POSSIBLE_DIRS[@]}"; do
    bin_path="$dir/$APP_NAME"
    if [ -f "$bin_path" ]; then
        echo "Removing leftover binary at $bin_path..."
        rm -f "$bin_path"
    fi
done

if [ -n "$ZDOTDIR" ]; then
  ZSHRC_FILE="$ZDOTDIR/.zshrc"
else
  ZSHRC_FILE="$HOME/.zshrc"
fi

if [ -f "$ZSHRC_FILE" ]; then
    echo "Checking for PATH modifications in $ZSHRC_FILE..."
    if grep -q "Added by setup-agent installer" "$ZSHRC_FILE"; then
        echo "Removing PATH entries added by the installer..."
        sed -i.bak '/Added by setup-agent installer/,+1d' "$ZSHRC_FILE"
        echo "✅ Removed PATH modification (backup at ${ZSHRC_FILE}.bak)"
    else
        echo "ℹ️ No setup-agent-specific PATH entry found in $ZSHRC_FILE."
    fi
else
    echo "ℹ️ No .zshrc file found — skipping PATH cleanup."
fi

echo ""
echo "Verifying uninstallation..."
if command -v "$APP_NAME" >/dev/null 2>&1; then
    echo "⚠️ $APP_NAME still detected on your PATH: $(command -v $APP_NAME)"
    echo "You may need to restart your terminal or manually remove it."
else
    echo "✅ $APP_NAME successfully uninstalled."
fi

echo ""
echo "✨ Uninstallation complete!"
