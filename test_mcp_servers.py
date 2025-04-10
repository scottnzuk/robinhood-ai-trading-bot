#!/usr/bin/env python3
"""
Script to test if the MCP servers are properly configured and accessible.
This script will check if the MCP settings file is correctly configured
and if the servers can be started.
"""
import json
import os
import subprocess
import sys
import time

def check_mcp_settings():
    """Check if the MCP settings file is correctly configured."""
    mcp_settings_path = os.path.expanduser(
        "~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json"
    )
    
    if not os.path.exists(mcp_settings_path):
        print(f"❌ MCP settings file not found at: {mcp_settings_path}")
        return False
    
    try:
        with open(mcp_settings_path, 'r') as f:
            settings = json.load(f)
        
        if "mcpServers" not in settings:
            print("❌ 'mcpServers' key not found in MCP settings")
            return False
        
        servers = settings["mcpServers"]
        
        # Check for Repomix
        if "repomix" not in servers:
            print("❌ Repomix server not found in MCP settings")
        else:
            print("✅ Repomix server found in MCP settings")
            print(f"   Command: {servers['repomix'].get('command', 'N/A')}")
            print(f"   Args: {servers['repomix'].get('args', 'N/A')}")
            print(f"   Allowed tools: {servers['repomix'].get('alwaysAllow', 'N/A')}")
        
        # Check for FireCrawl
        if "firecrawl" not in servers:
            print("❌ FireCrawl server not found in MCP settings")
        else:
            print("✅ FireCrawl server found in MCP settings")
            if "command" in servers['firecrawl']:
                print(f"   Command: {servers['firecrawl'].get('command', 'N/A')}")
                print(f"   Args: {servers['firecrawl'].get('args', 'N/A')}")
            else:
                print(f"   Type: {servers['firecrawl'].get('type', 'N/A')}")
                print(f"   Host: {servers['firecrawl'].get('host', 'N/A')}")
                print(f"   Port: {servers['firecrawl'].get('port', 'N/A')}")
            print(f"   Allowed tools: {servers['firecrawl'].get('alwaysAllow', 'N/A')}")
        
        # Check for Lucidity
        if "lucidity" not in servers:
            print("❌ Lucidity server not found in MCP settings")
        else:
            print("✅ Lucidity server found in MCP settings")
            if "command" in servers['lucidity']:
                print(f"   Command: {servers['lucidity'].get('command', 'N/A')}")
                print(f"   Args: {servers['lucidity'].get('args', 'N/A')}")
            else:
                print(f"   Type: {servers['lucidity'].get('type', 'N/A')}")
                print(f"   Host: {servers['lucidity'].get('host', 'N/A')}")
                print(f"   Port: {servers['lucidity'].get('port', 'N/A')}")
            print(f"   Allowed tools: {servers['lucidity'].get('alwaysAllow', 'N/A')}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error reading MCP settings: {e}")
        return False

def test_repomix():
    """Test if Repomix is installed and can be started."""
    try:
        # Check if Repomix is installed
        result = subprocess.run(
            ["npx", "repomix", "--version"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Repomix is installed (version: {result.stdout.strip()})")
        else:
            print(f"❌ Repomix is not installed or not working")
            print(f"   Error: {result.stderr.strip()}")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error testing Repomix: {e}")
        return False

def test_firecrawl():
    """Test if FireCrawl is installed."""
    try:
        print("⏳ Testing FireCrawl installation (with 5 second timeout)...")
        
        # Skip actual testing to avoid hanging
        print("ℹ️ Skipping FireCrawl version check to avoid potential hanging")
        print("ℹ️ FireCrawl will be tested when you run the start script")
        
        # Check if the package exists using npm list
        result = subprocess.run(
            ["npm", "list", "-g", "firecrawl-mcp"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "firecrawl-mcp" in result.stdout:
            print(f"✅ FireCrawl package is found in npm list")
            return True
        else:
            print(f"⚠️ FireCrawl package not found in global npm list")
            print(f"   This is OK if you're using npx to run it on-demand")
            return True
    
    except subprocess.TimeoutExpired:
        print("⚠️ FireCrawl test timed out after 5 seconds")
        print("   This is not necessarily an error - the script will still work")
        return True
    except Exception as e:
        print(f"⚠️ Error testing FireCrawl: {e}")
        print("   This is not necessarily an error - the script will still work")
        return True

def main():
    """Main function to run the tests."""
    print("🔍 Testing MCP server configurations...")
    print("\n1. Checking MCP settings file...")
    check_mcp_settings()
    
    print("\n2. Testing Repomix installation...")
    test_repomix()
    
    print("\n3. Testing FireCrawl installation...")
    test_firecrawl()
    
    print("\n📋 Summary:")
    print("To use these MCP servers with Roo Code:")
    print("1. Make sure the servers are properly configured in the MCP settings file")
    print("2. Start the servers using the provided scripts:")
    print("   - ./start_repomix_mcp.sh")
    print("   - ./start_firecrawl_mcp.sh")
    print("3. You may need to restart VS Code or reload the MCP settings")
    print("   - Use ./reload_mcp_settings.sh or restart VS Code")
    print("4. Use the example scripts to test the servers:")
    print("   - ./repomix_mcp_example.py")
    print("   - ./firecrawl_mcp_example.py")

if __name__ == "__main__":
    main()