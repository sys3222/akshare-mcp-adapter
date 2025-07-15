import pytest
from fastapi.testclient import TestClient
import os
import shutil
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta

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

# --- Cache Status API Tests ---

def test_cache_status_unauthenticated():
    """Tests that /cache/status requires authentication."""
    response = client.get("/api/cache/status")
    assert response.status_code == 401

def test_cache_status_empty_cache(auth_headers):
    """Tests cache status when cache directory is empty."""
    response = client.get("/api/cache/status", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "cache_directory" in data
    assert "total_files" in data
    assert "total_size_mb" in data
    assert "files" in data
    assert data["total_files"] == 0
    assert data["total_size_mb"] == 0
    assert data["files"] == []

def test_cache_status_with_files(auth_headers):
    """Tests cache status when cache directory has files."""
    # 创建临时缓存文件
    cache_dir = Path("static/cache/system")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 创建测试缓存文件
    test_file1 = cache_dir / "test_cache_1.parquet"
    test_file2 = cache_dir / "test_cache_2.parquet"

    # 写入一些测试数据
    test_content = b"test parquet data"
    test_file1.write_bytes(test_content)
    test_file2.write_bytes(test_content * 2)  # 不同大小

    try:
        response = client.get("/api/cache/status", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total_files"] == 2
        assert data["total_size_mb"] > 0
        assert len(data["files"]) == 2

        # 检查文件信息结构
        for file_info in data["files"]:
            assert "filename" in file_info
            assert "size_mb" in file_info
            assert "modified_time" in file_info
            assert "age_hours" in file_info
            assert file_info["filename"] in ["test_cache_1.parquet", "test_cache_2.parquet"]
            assert file_info["size_mb"] >= 0
            assert file_info["age_hours"] >= 0

    finally:
        # 清理测试文件
        if test_file1.exists():
            test_file1.unlink()
        if test_file2.exists():
            test_file2.unlink()

def test_cache_status_file_sorting(auth_headers):
    """Tests that cache status files are sorted by modification time (newest first)."""
    cache_dir = Path("static/cache/system")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 创建两个文件，设置不同的修改时间
    old_file = cache_dir / "old_cache.parquet"
    new_file = cache_dir / "new_cache.parquet"

    old_file.write_bytes(b"old data")
    new_file.write_bytes(b"new data")

    # 设置旧文件的修改时间为1小时前
    old_time = (datetime.now() - timedelta(hours=1)).timestamp()
    os.utime(old_file, (old_time, old_time))

    try:
        response = client.get("/api/cache/status", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["files"]) == 2

        # 检查文件按修改时间排序（最新的在前）
        files = data["files"]
        assert files[0]["filename"] == "new_cache.parquet"
        assert files[1]["filename"] == "old_cache.parquet"
        assert files[0]["age_hours"] < files[1]["age_hours"]

    finally:
        # 清理测试文件
        if old_file.exists():
            old_file.unlink()
        if new_file.exists():
            new_file.unlink()

def test_cache_status_error_handling(auth_headers):
    """Tests cache status error handling when cache directory doesn't exist."""
    # 确保缓存目录不存在
    cache_dir = Path("static/cache/system")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    response = client.get("/api/cache/status", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total_files"] == 0
    assert data["total_size_mb"] == 0
    assert data["files"] == []