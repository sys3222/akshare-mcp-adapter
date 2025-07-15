import pytest
from fastapi.testclient import TestClient
import os
import shutil
from pathlib import Path

# Add project root to path to allow importing 'main'
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from create_user import create_user
from core.database import SessionLocal, create_db_and_tables

client = TestClient(app)

# --- Test Setup and Teardown ---

@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_test_users():
    """Create test users before tests run and clean up after."""
    # Ensure the tables are created before the session starts
    create_db_and_tables()
    db = SessionLocal()
    try:
        # Setup: Create test users
        create_user(db, "testuser", "testpassword")
        create_user(db, "testuser2", "testpassword2")
    finally:
        db.close()
    
    yield # This is where the tests will run
    
    # Teardown: Clean up created resources
    db_file = Path("mcp_app.db")
    if db_file.exists():
        db_file.unlink()
        
    cache_dir = Path("static/cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

# --- Fixtures ---

@pytest.fixture(scope="module")
def auth_headers():
    """Fixture to get authentication headers for 'testuser'."""
    response = client.post("/api/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def auth_headers_user2():
    """Fixture to get authentication headers for 'testuser2'."""
    response = client.post("/api/token", data={"username": "testuser2", "password": "testpassword2"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# --- Core API Tests ---

def test_health_check():
    """Tests the /health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login_and_get_me(auth_headers):
    """Tests login and the /users/me endpoint."""
    response = client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_mcp_data_request_unauthenticated():
    """Tests that /mcp-data requires authentication."""
    response = client.post("/api/mcp-data", json={})
    assert response.status_code == 401

# --- File Management and Exploration Tests ---

def test_file_management_flow(auth_headers):
    """Tests the full file management lifecycle: upload, list, explore, delete."""
    
    # 1. Initial state: No files
    response = client.get("/api/data/files", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

    # 2. Upload a file
    test_file_path = Path("tests/data/test_upload.csv")
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_upload.csv", f, "text/csv")}
        response = client.post("/api/data/upload", files=files, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["filename"] == "test_upload.csv"

    # 3. List files and see the new file
    response = client.get("/api/data/files", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == ["test_upload.csv"]

    # 4. Explore the uploaded file's content
    response = client.post("/api/data/explore/test_upload.csv", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 2
    assert data["current_page"] == 1
    assert data["data"] == [{"col1": "val1", "col2": "val2"}, {"col1": "val3", "col2": "val4"}]

    # 5. Delete the file
    response = client.delete("/api/data/files/test_upload.csv", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["detail"] == "File deleted successfully."

    # 6. Final state: No files again
    response = client.get("/api/data/files", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

def test_file_security_isolation(auth_headers, auth_headers_user2):
    """Tests that one user cannot access another user's files."""
    
    # User 1 uploads a file
    test_file_path = Path("tests/data/test_upload.csv")
    with open(test_file_path, "rb") as f:
        files = {"file": ("user1_file.csv", f, "text/csv")}
        response = client.post("/api/data/upload", files=files, headers=auth_headers)
    assert response.status_code == 200

    # User 2 should not see User 1's file
    response = client.get("/api/data/files", headers=auth_headers_user2)
    assert response.status_code == 200
    assert response.json() == []

    # User 2 cannot explore User 1's file
    response = client.post("/api/data/explore/user1_file.csv", headers=auth_headers_user2)
    assert response.status_code == 404

    # User 2 cannot delete User 1's file
    response = client.delete("/api/data/files/user1_file.csv", headers=auth_headers_user2)
    assert response.status_code == 404

    # Cleanup: User 1 deletes their file
    response = client.delete("/api/data/files/user1_file.csv", headers=auth_headers)
    assert response.status_code == 200