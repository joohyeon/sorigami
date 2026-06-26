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
    valid_user_id = str(uuid4())
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    response = client.get(f"/modes?user_id={valid_user_id}")
    assert response.status_code == 200

def test_list_modes_invalid_uuid(client, mock_supabase):
    response = client.get("/modes?user_id=not-a-uuid")
    assert response.status_code == 422

def test_delete_mode_ownership(client, mock_supabase):
    mode_id = str(uuid4())
    owner_id = str(uuid4())
    other_id = str(uuid4())
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "id": mode_id, "user_id": owner_id
    }
    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
    # Correct owner → 204
    response = client.delete(f"/modes/{mode_id}?user_id={owner_id}")
    assert response.status_code == 204
    # Wrong owner → 403
    response = client.delete(f"/modes/{mode_id}?user_id={other_id}")
    assert response.status_code == 403

def test_delete_mode_not_found(client, mock_supabase):
    mode_id = str(uuid4())
    user_id = str(uuid4())
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    response = client.delete(f"/modes/{mode_id}?user_id={user_id}")
    assert response.status_code == 404

def test_update_mode_ownership(client, mock_supabase):
    mode_id = str(uuid4())
    owner_id = str(uuid4())
    other_id = str(uuid4())
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "id": mode_id, "user_id": owner_id
    }
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        {"id": mode_id, "name": "Updated", "skill_ids": []}
    ]
    # Wrong owner → 403
    response = client.put(f"/modes/{mode_id}?user_id={other_id}", json={"name": "Updated"})
    assert response.status_code == 403
