"""
Phi model integration for AI trading.
"""
import os
import json
import torch
from typing import Dict, List, Any, Optional
from my_transformers_extensions import AutoModelForCausalLM, AutoTokenizer

class PhiModel:
    """
    Wrapper for the quantized phi model for trading decisions.
    
    This class handles loading the model, generating responses, and
    formatting the output for the AI trading engine.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the phi model.
        
        Args:
            model_path: Path to the model directory (default: None, will use default path)
        """
        self.model_path = model_path or os.path.expanduser("~/models/phi-2")
        self.model = None
        self.tokenizer = None
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
        self.max_length = 2048
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        Load the model and tokenizer.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            print(f"Loading phi model from {self.model_path} on {self.device}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Load model with quantization for efficiency
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
            self.initialized = True
            print("Phi model loaded successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing phi model: {str(e)}")
            return False
    
    def generate_response(self, prompt: str) -> Optional[str]:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The generated response or None if there was an error
        """
        if not self.initialized:
            if not self.initialize():
                return None
        
        try:
            # Tokenize the prompt
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=self.max_length,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the model's response (everything after the prompt)
            response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            print(f"Error generating response from phi model: {str(e)}")
            return None
    
    def extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from the model's response.
        
        Args:
            response: The model's response
            
        Returns:
            Parsed JSON or None if no valid JSON was found
        """
        if not response:
            return None
        
        try:
            # Find JSON-like content (between curly braces)
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
            
        except json.JSONDecodeError:
            print("Failed to parse JSON from response")
            return None
    
    def analyze_market(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze market data and generate trading recommendations.
        
        Args:
            context: Market data and context for analysis
            
        Returns:
            Dictionary of trading recommendations or None if there was an error
        """
        # Create a prompt for the phi model
        prompt = self._create_prompt(context)
        
        # Generate response
        response = self.generate_response(prompt)
        if not response:
            return None
        
        # Extract JSON from response
        recommendations = self.extract_json_from_response(response)
        
        return recommendations
    
    def _create_prompt(self, context: Dict[str, Any]) -> str:
        """
        Create a prompt for the phi model based on the context.
        
        Args:
            context: Market data and context for analysis
            
        Returns:
            Formatted prompt string
        """
        # Create a simpler prompt optimized for phi's smaller context window
        prompt = """You are an expert financial advisor analyzing market data. Provide trading recommendations based on this data.

MARKET DATA:
"""
        
        # Add simplified market data
        if "market_summary" in context:
            prompt += f"\nMarket Summary: {context['market_summary']}\n"
        
        if "symbols" in context:
            prompt += "\nSymbols:\n"
            for symbol, data in context["symbols"].items():
                prompt += f"- {symbol}: Price ${data.get('close', 'N/A')}, Change: {data.get('percent_change', 'N/A')}%\n"
        
        # Add instructions for response format
        prompt += """
Analyze this data and provide trading recommendations in JSON format:

{
    "recommendations": [
        {
            "symbol": "TICKER",
            "decision": "buy/sell/hold",
            "confidence": 0.85,
            "reasoning": "Brief explanation"
        }
    ]
}

JSON Response:
"""
        
        return prompt
