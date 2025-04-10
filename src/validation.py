import json
from typing import List, Dict, Union, Any, Optional
from src.exceptions import InvalidAIResponseError

class ValidationError(Exception):
    """Raised when input validation fails"""
    pass

def validate_input(data: Any, schema: Dict) -> Any:
    """Validate input data against a schema
    
    Args:
        data: The data to validate
        schema: Schema definition for validation
        
    Returns:
        The validated data if validation passes
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Check the type of the data
        if schema.get('type') == 'object' and not isinstance(data, dict):
            raise ValidationError(f"Expected object, got {type(data)}")
        elif schema.get('type') == 'array' and not isinstance(data, list):
            raise ValidationError(f"Expected array, got {type(data)}")
        elif schema.get('type') == 'string' and not isinstance(data, str):
            raise ValidationError(f"Expected string, got {type(data)}")
        elif schema.get('type') == 'integer' and not isinstance(data, int):
            raise ValidationError(f"Expected integer, got {type(data)}")
        elif schema.get('type') == 'number' and not isinstance(data, (int, float)):
            raise ValidationError(f"Expected number, got {type(data)}")
        elif schema.get('type') == 'boolean' and not isinstance(data, bool):
            raise ValidationError(f"Expected boolean, got {type(data)}")
            
        if 'required' in schema:
            for field in schema['required']:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")
                    
        if 'properties' in schema:
            for field, field_schema in schema['properties'].items():
                if field in data:
                    validate_input(data[field], field_schema)
                    
        return data
    except ValidationError as e:
        raise e
    except Exception as e:
        raise ValidationError(str(e))

class AIResponseValidator:
    """Validates AI decision responses before execution"""
    
    def validate(self, response: Dict) -> Dict:
        """Validate a single AI response
        
        Args:
            response: The AI response to validate
            
        Returns:
            The validated response if validation passes
            
        Raises:
            InvalidAIResponseError: If validation fails
        """
        if not isinstance(response, dict):
            raise InvalidAIResponseError("AI response must be a dictionary")
            
        required_fields = ["decision", "ticker"]
        for field in required_fields:
            if field not in response:
                raise InvalidAIResponseError(f"Missing required field: {field}")
                
        if response["decision"] not in ("BUY", "SELL", "HOLD"):
            raise InvalidAIResponseError(f"Invalid decision type: {response['decision']}")
            
        if "confidence" in response and not isinstance(response["confidence"], (int, float)):
            raise InvalidAIResponseError(f"Confidence must be a number")
            
        return response
        
    @staticmethod
    def validate_structure(decisions: List[Dict]) -> bool:
        """Validate basic response structure"""
        if not isinstance(decisions, list):
            raise InvalidAIResponseError("AI response must be a list")
            
        for decision in decisions:
            if not all(k in decision for k in ("symbol", "decision", "quantity")):
                raise InvalidAIResponseError(
                    "Each decision must contain symbol, decision and quantity"
                )
                
            if decision["decision"] not in ("buy", "sell", "hold"):
                raise InvalidAIResponseError(
                    f"Invalid decision type: {decision['decision']}"
                )
                
            try:
                float(decision["quantity"])
            except ValueError:
                raise InvalidAIResponseError(
                    f"Invalid quantity: {decision['quantity']}"
                )
                
        return True

    @staticmethod
    def validate_content(decisions: List[Dict], portfolio: Dict) -> bool:
        """Validate decisions against current portfolio"""
        for decision in decisions:
            symbol = decision["symbol"]
            
            # Validate sell decisions
            if decision["decision"] == "sell":
                if symbol not in portfolio:
                    raise InvalidAIResponseError(
                        f"Cannot sell {symbol} - not in portfolio"
                    )
                    
            # Validate quantity
            if decision["decision"] in ("buy", "sell"):
                if float(decision["quantity"]) <= 0:
                    raise InvalidAIResponseError(
                        f"Invalid quantity for {symbol}: {decision['quantity']}"
                    )
                    
        return True

    @classmethod
    def full_validation(cls, decisions: Union[List[Dict], str], portfolio: Dict) -> List[Dict]:
        """Perform complete validation of AI response
        
        Args:
            decisions: The decisions to validate, either as a JSON string or list of dicts
            portfolio: Current portfolio holdings
            
        Returns:
            The validated decisions
            
        Raises:
            InvalidAIResponseError: If validation fails
        """
        if isinstance(decisions, str):
            try:
                decisions = json.loads(decisions)
            except json.JSONDecodeError:
                raise InvalidAIResponseError("Invalid JSON response")
                
        cls.validate_structure(decisions)
        cls.validate_content(decisions, portfolio)
        return decisions