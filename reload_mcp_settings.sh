#!/bin/bash

echo "Reloading MCP settings for Roo Code..."

# Option 1: Create a temporary file that will trigger a reload
touch "/Users/byteme/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json"

echo "MCP settings have been touched to trigger a reload."
echo ""
echo "If this doesn't work, please try one of these methods:"
echo "1. Open the Command Palette in VS Code (Cmd+Shift+P)"
echo "2. Type 'Roo: Reload MCP' or similar and select if available"
echo "3. If no such command exists, restart VS Code to apply the changes"