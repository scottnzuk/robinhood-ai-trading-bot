import pytest
from unittest.mock import patch, AsyncMock
from src.api.robinhood import RobinhoodClient

@pytest.fixture
def client():
    return RobinhoodClient()

@patch('src.api.robinhood.requests.post', new_callable=AsyncMock)
async def test_login_success(mock_post, client):
    mock_post.return_value.status_code = 200
    result = await client.login("user", "pass")
    assert result is None or result is True  # login returns None or True on success

@patch('src.api.robinhood.requests.get', new_callable=AsyncMock)
async def test_get_account_info_success(mock_get, client):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"equity": 1000}
    info = await client.get_account_info()
    assert isinstance(info, dict)
    assert "equity" in info