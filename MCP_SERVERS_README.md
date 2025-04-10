# MCP Servers Setup

This document explains how the Model Context Protocol (MCP) servers are set up in this project.

## Configured MCP Servers

### 1. Repomix MCP Server

Repomix is an MCP server that allows AI assistants to package local or remote repositories for analysis.

**Features:**
- Package local code directories
- Fetch and package GitHub repositories
- Read packaged codebase content
- Safe file system operations

### 2. FireCrawl MCP Server

FireCrawl is an MCP server for web crawling and data extraction.

**Features:**
- Crawl websites
- Search for content
- Extract data using selectors

### 3. Lucidity MCP Server

Lucidity is an MCP server designed to enhance the quality of AI-generated code through intelligent, prompt-based analysis.

**Features:**
- Comprehensive issue detection across 10 quality dimensions
- Contextual analysis comparing changes against original code
- Language-agnostic code quality analysis
- Structured outputs with actionable feedback

## Auto-Start Configuration

The MCP servers are configured to auto-start when VS Code opens this project. This is done using VS Code tasks:

1. `.vscode/tasks.json` - Defines the tasks to start the MCP servers
2. `.vscode/settings.json` - Enables automatic task execution

When you open this project in VS Code, three terminal windows should automatically open and start the MCP servers.

## Manual Start

If the servers don't start automatically, you can start them manually:

```bash
# Start Repomix MCP server
./start_repomix_mcp.sh

# Start FireCrawl MCP server
./start_firecrawl_mcp.sh

# Start Lucidity MCP server
./start_lucidity_mcp.sh
```

## Testing the Setup

You can test if the MCP servers are properly configured and accessible:

```bash
./test_mcp_servers.py
```

## Example Usage

### Repomix Example

```bash
# Package a local codebase
./repomix_mcp_example.py local /path/to/your/project

# Package a remote GitHub repository
./repomix_mcp_example.py remote username/repository
```

### FireCrawl Example

```bash
# Crawl a website
./firecrawl_mcp_example.py crawl https://example.com 2 20

# Search for content
./firecrawl_mcp_example.py search "your search query"

# Extract data using a CSS selector
./firecrawl_mcp_example.py extract https://example.com "div.main-content"
```

### Lucidity Example

With an AI assistant connected to Lucidity, try these queries:

```
# Analyze code quality
"Analyze the code quality in my latest git changes"

# Check for specific issues
"Check for security vulnerabilities in my JavaScript changes"
"Make sure my Python code follows best practices"
"Identify any performance issues in my recent code changes"

# Validate refactoring
"Are there any unintended side effects in my recent refactoring?"
"Help me improve the abstractions in my code"
"Check if I've accidentally removed any important validation"
```

## Reloading MCP Settings

If you make changes to the MCP settings, you can reload them:

```bash
./reload_mcp_settings.sh
```

Or restart VS Code to ensure the settings are reloaded.

## MCP Settings Location

The MCP settings are stored in:

```
~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json
```

This file contains the configuration for all MCP servers that Roo Code can access.