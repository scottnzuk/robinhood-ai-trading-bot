#!/bin/bash

LOG_DIR="/mnt/c/mcp_logs"
mkdir -p "$LOG_DIR"

ARCH_NAME=$(uname -m)
if [[ "$ARCH_NAME" != "arm64" ]]; then
    echo "WARNING: Non-arm64 architecture detected: $ARCH_NAME"
fi

# Lucidity MCP (DISABLED)
: '
if ! pgrep -f "lucidity-mcp" > /dev/null; then
    LUCIDITY_DIR="lucidity-mcp"
    VENV_PATH="$LUCIDITY_DIR/.venv"
    if [ ! -d "$VENV_PATH" ]; then
        arch -arm64 python3 -m venv "$VENV_PATH"
    fi
    source "$VENV_PATH/bin/activate"
    arch -arm64 pip install --upgrade pip setuptools wheel
    if [ -f "$LUCIDITY_DIR/pyproject.toml" ]; then
        arch -arm64 pip install --upgrade --editable "$LUCIDITY_DIR"
    fi
    arch -arm64 lucidity-mcp --transport sse --host 127.0.0.1 --port 9904 --debug --verbose > "$LOG_DIR/lucidity_mcp.log" 2>&1 &
fi
'

# Repomix MCP (DISABLED)
: '
if ! pgrep -f "npx repomix --mcp" > /dev/null; then
    arch -arm64 npx repomix --mcp --port 9905 > "$LOG_DIR/repomix_mcp.log" 2>&1 &
fi
'

# UltimateCoder MCP
if ! pgrep -f "npx ultimatecoder" > /dev/null; then
    arch -arm64 npx ultimatecoder --mcp --port 9906 > "$LOG_DIR/ultimatecoder_mcp.log" 2>&1 &
fi

# DeepSeekG MCP
if ! pgrep -f "npx deepseekg" > /dev/null; then
    arch -arm64 npx deepseekg --mcp --port 9907 > "$LOG_DIR/deepseekg_mcp.log" 2>&1 &
fi

# Firecrawl MCP
if ! pgrep -f "npx firecrawl-mcp-server" > /dev/null; then
    arch -arm64 npx firecrawl-mcp-server --port 9908 > "$LOG_DIR/firecrawl_mcp.log" 2>&1 &
fi

# RAGDocs MCP
if ! pgrep -f "ragdocs_server.py" > /dev/null; then
    RAGDOCS_DIR="mcp_sources/mcp-ragdocs"
    VENV_PATH="$RAGDOCS_DIR/.venv"
    if [ ! -d "$VENV_PATH" ]; then
        arch -arm64 python3 -m venv "$VENV_PATH"
    fi
    source "$VENV_PATH/bin/activate"
    arch -arm64 pip install --upgrade pip setuptools wheel
    arch -arm64 python3 $RAGDOCS_DIR/ragdocs_server.py --port 9909 > "$LOG_DIR/ragdocs_mcp.log" 2>&1 &
fi

# SequentialThinking MCP
if ! pgrep -f "sequentialthinking_server.py" > /dev/null; then
    SEQ_DIR="mcp_sources/mcp-sequentialthinking-tools"
    VENV_PATH="$SEQ_DIR/.venv"
    if [ ! -d "$VENV_PATH" ]; then
        arch -arm64 python3 -m venv "$VENV_PATH"
    fi
    source "$VENV_PATH/bin/activate"
    arch -arm64 pip install --upgrade pip setuptools wheel
    arch -arm64 python3 $SEQ_DIR/sequentialthinking_server.py --port 9910 > "$LOG_DIR/sequentialthinking_mcp.log" 2>&1 &
fi

# CodeResearch MCP
if ! pgrep -f "coderesearch_server.py" > /dev/null; then
    CR_DIR="mcp_sources/code-research-mcp-server"
    VENV_PATH="$CR_DIR/.venv"
    if [ ! -d "$VENV_PATH" ]; then
        arch -arm64 python3 -m venv "$VENV_PATH"
    fi
    source "$VENV_PATH/bin/activate"
    arch -arm64 pip install --upgrade pip setuptools wheel
    arch -arm64 python3 $CR_DIR/coderesearch_server.py --port 9911 > "$LOG_DIR/coderesearch_mcp.log" 2>&1 &
fi

wait