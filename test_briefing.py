import pytest
from unittest.mock import patch, AsyncMock
from ollama_client import ask_ollama

@pytest.mark.asyncio
async def test_ask_ollama_with_system_prompt():
    from unittest.mock import MagicMock
    with patch('ollama_client.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Test response"}}
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        custom_system = "You are a custom assistant."
        await ask_ollama(
            base_url="http://localhost:11434",
            model="test-model",
            prompt="Hello",
            system_prompt=custom_system
        )
        
        # Verify the payload has the custom system prompt
        call_args = mock_client.post.call_args
        assert call_args is not None
        
        # httpx post payload is in kwargs "json"
        payload = call_args.kwargs.get("json")
        messages = payload.get("messages")
        
        system_message = next((m for m in messages if m["role"] == "system"), None)
        assert system_message is not None
        assert system_message["content"] == custom_system

@pytest.mark.asyncio
async def test_ask_ollama_default_system_prompt():
    from unittest.mock import MagicMock
    with patch('ollama_client.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Test response"}}
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        await ask_ollama(
            base_url="http://localhost:11434",
            model="test-model",
            prompt="Hello"
        )
        
        call_args = mock_client.post.call_args
        assert call_args is not None
        
        payload = call_args.kwargs.get("json")
        messages = payload.get("messages")
        
        system_message = next((m for m in messages if m["role"] == "system"), None)
        assert system_message is not None
        # It should contain the default name, e.g. from config
        assert "あなたの名前は" in system_message["content"]
