#!/bin/bash

echo "=== VSCode Terminal Reset Script ==="

echo "1. Fully quitting VSCode..."
osascript -e 'quit app "Visual Studio Code"'
sleep 3

echo "2. Removing VSCode cached terminal data and workspace storage..."
rm -rf ~/Library/Application\ Support/Code/CachedData
rm -rf ~/Library/Application\ Support/Code/User/workspaceStorage

echo "3. Resetting shell integration settings (manual step recommended):"
echo "   - Open VSCode after this script completes."
echo "   - Press Cmd+Shift+P → 'Preferences: Open Settings (UI)'."
echo "   - Search 'terminal.integrated.shellIntegration.enabled' and toggle it OFF."
echo "   - Close all integrated terminals."
echo "   - Open a new terminal, then optionally toggle it ON again."

echo "4. Updating VSCode and extensions (manual step recommended):"
echo "   - Cmd+Shift+P → 'Check for Updates' → update if available."
echo "   - Cmd+Shift+P → 'Extensions: Check for Updates' → update all extensions."

echo "5. Resetting default shell (manual step recommended):"
echo "   - Cmd+Shift+P → 'Terminal: Select Default Profile'."
echo "   - Choose 'zsh' or 'bash'. Avoid 'fish' or custom shells."

