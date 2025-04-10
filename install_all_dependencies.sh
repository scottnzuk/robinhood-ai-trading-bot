#!/bin/bash

echo "Installing dependencies for root project..."
pip install .

echo "Installing dependencies for nested robinhood-ai-trading-bot/"
cd robinhood-ai-trading-bot
pip install .
cd ..

echo "Installing dependencies for lucidity-mcp/"
cd lucidity-mcp
pip install .
cd ..

echo "All dependencies installed successfully."