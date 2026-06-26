from uuid import uuid4

MODE = {"name": "My Mode", "skill_ids": [str(uuid4())]}

def test_create_mode(client, mock_supabase):
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": str(uuid4()), **MODE}
    ]
    response = client.post("/modes", json=MODE)
    assert response.status_code == 201
    assert response.json()["name"] == "My Mode"

def test_list_modes(client, mock_supabase):
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = []
    response = client.get("/modes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_modes_with_user_id(client, mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    response = client.get("/modes?user_id=user-123")
    assert response.status_code == 200
