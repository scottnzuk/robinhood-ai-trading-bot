import pytest
from src.validation import validate_input, ValidationError, AIResponseValidator
from src.exceptions import InvalidAIResponseError


def test_validate_input_success():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name"]
    }
    
    data = {"name": "John", "age": 30}
    result = validate_input(data, schema)
    assert result == data


def test_validate_input_failure():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }
    
    data = {"name": "John"}
    with pytest.raises(ValidationError):
        validate_input(data, schema)


def test_ai_response_validator():
    validator = AIResponseValidator()
    
    # Valid response
    valid_response = {
        "decision": "BUY",
        "ticker": "AAPL",
        "confidence": 0.85,
        "analysis": "Strong earnings report"
    }
    
    assert validator.validate(valid_response) == valid_response
    
    # Invalid response - missing required field
    invalid_response = {
        "decision": "BUY",
        "confidence": 0.85,
        "analysis": "Strong earnings report"
    }
    
    with pytest.raises(InvalidAIResponseError):
        validator.validate(invalid_response)
