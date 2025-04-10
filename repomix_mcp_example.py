#!/usr/bin/env python3
"""
Example script demonstrating how to use the Repomix MCP server.
"""
import json
import os
import sys
import requests

# MCP server configuration
MCP_SERVER = "repomix"
MCP_PORT = 8000  # Default port for Repomix MCP server

def call_mcp_tool(tool_name, params):
    """Call an MCP tool on the Repomix server."""
    url = f"http://localhost:{MCP_PORT}/tools/{tool_name}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=params)
    
    if response.status_code != 200:
        print(f"Error calling {tool_name}: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def pack_local_codebase(directory, compress=True, include_patterns=None, ignore_patterns=None):
    """Package a local code directory for AI analysis."""
    params = {
        "directory": os.path.abspath(directory),
        "compress": compress
    }
    
    if include_patterns:
        params["includePatterns"] = include_patterns
    
    if ignore_patterns:
        params["ignorePatterns"] = ignore_patterns
    
    result = call_mcp_tool("pack_codebase", params)
    if result:
        print(f"Successfully packed codebase from {directory}")
        print(f"Output ID: {result.get('outputId')}")
        print(f"Output Path: {result.get('outputPath')}")
        return result
    return None

def pack_remote_repository(repo_url, compress=True, include_patterns=None, ignore_patterns=None):
    """Fetch, clone, and package a GitHub repository for AI analysis."""
    params = {
        "remote": repo_url,
        "compress": compress
    }
    
    if include_patterns:
        params["includePatterns"] = include_patterns
    
    if ignore_patterns:
        params["ignorePatterns"] = ignore_patterns
    
    result = call_mcp_tool("pack_remote_repository", params)
    if result:
        print(f"Successfully packed repository from {repo_url}")
        print(f"Output ID: {result.get('outputId')}")
        print(f"Output Path: {result.get('outputPath')}")
        return result
    return None

def read_repomix_output(output_id):
    """Read the contents of a Repomix output file."""
    params = {
        "outputId": output_id
    }
    
    result = call_mcp_tool("read_repomix_output", params)
    if result:
        print(f"Successfully read output with ID: {output_id}")
        return result.get("content")
    return None

def read_file(file_path):
    """Read a file using Repomix's file system tool."""
    params = {
        "path": os.path.abspath(file_path)
    }
    
    result = call_mcp_tool("file_system_read_file", params)
    if result:
        print(f"Successfully read file: {file_path}")
        return result.get("content")
    return None

def list_directory(dir_path):
    """List directory contents using Repomix's file system tool."""
    params = {
        "path": os.path.abspath(dir_path)
    }
    
    result = call_mcp_tool("file_system_read_directory", params)
    if result:
        print(f"Successfully listed directory: {dir_path}")
        return result.get("entries")
    return None

def main():
    """Main function demonstrating Repomix MCP usage."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Local codebase:  python repomix_mcp_example.py local <directory>")
        print("  Remote repo:     python repomix_mcp_example.py remote <repo_url>")
        return
    
    mode = sys.argv[1]
    
    if mode == "local" and len(sys.argv) >= 3:
        directory = sys.argv[2]
        result = pack_local_codebase(directory)
        if result and result.get("outputId"):
            # Optionally read the output
            # content = read_repomix_output(result.get("outputId"))
            pass
    
    elif mode == "remote" and len(sys.argv) >= 3:
        repo_url = sys.argv[2]
        result = pack_remote_repository(repo_url)
        if result and result.get("outputId"):
            # Optionally read the output
            # content = read_repomix_output(result.get("outputId"))
            pass
    
    else:
        print("Invalid mode or missing arguments")

if __name__ == "__main__":
    main()