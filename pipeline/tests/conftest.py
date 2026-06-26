import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_supabase():
    return MagicMock()

@pytest.fixture
def client(mock_supabase):
    with patch("supabase_client.get_supabase", return_value=mock_supabase):
        from main import app
        return TestClient(app)
