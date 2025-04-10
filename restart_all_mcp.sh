#!/bin/bash
set -e

echo "Stopping any existing MCP servers..."
pkill -f repomix || true
pkill -f firecrawl-mcp || true
pkill -f lucidity-mcp || true

echo "Starting Repomix MCP server with HTTPS..."
nohup bash start_repomix_mcp.sh > repomix_mcp.log 2>&1 &

echo "Starting FireCrawl MCP server with HTTPS..."
nohup bash start_firecrawl_mcp.sh > firecrawl_mcp.log 2>&1 &

echo "Starting Lucidity MCP server with HTTPS..."
nohup bash start_lucidity_mcp.sh > lucidity_mcp.log 2>&1 &

echo "All MCP servers restarted with HTTPS."