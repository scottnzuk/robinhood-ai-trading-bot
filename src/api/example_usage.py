"""
Example Usage of AI Providers

Demonstrates basic usage of AI providers for trading decisions.
"""

import os
from src.api.openai_client import (
    AIProvider,
    make_ai_request
)

def test_ai_provider(provider: AIProvider = AIProvider.REQUESTY):
    """
    Test AI provider with a sample prompt.
    
    Args:
        provider: AI provider to test
    """
    prompt = "Hello, who are you? Please respond with a short introduction."
    model = "openai/gpt-4o-mini-2024-07-18"
    
    try:
        response = make_ai_request(prompt, provider, model)
        
        if isinstance(response, dict) and 'choices' in response:
            print(response['choices'][0]['message']['content'])
        else:
            print("Unexpected response format:", response)
    except Exception as e:
        print(f"Error with {provider.value}: {str(e)}")

if __name__ == "__main__":
    test_ai_provider()