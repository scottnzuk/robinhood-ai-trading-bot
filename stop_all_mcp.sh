#!/bin/bash

echo "Stopping all MCP servers..."

pkill -f "lucidity-mcp" && echo "Stopped Lucidity MCP."
pkill -f "npx repomix --mcp" && echo "Stopped Repomix MCP."
pkill -f "npx ultimatecoder" && echo "Stopped UltimateCoder MCP."
pkill -f "npx deepseekg" && echo "Stopped DeepSeekG MCP."
pkill -f "npx firecrawl-mcp-server" && echo "Stopped Firecrawl MCP."
pkill -f "ragdocs_server.py" && echo "Stopped RAGDocs MCP."
pkill -f "sequentialthinking_server.py" && echo "Stopped SequentialThinking MCP."
pkill -f "coderesearch_server.py" && echo "Stopped CodeResearch MCP."

echo "All MCP servers stop commands issued."