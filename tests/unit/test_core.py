
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from core.database import Base, User, get_db
from datetime import timedelta

# --- Tests for core/security.py ---

def test_password_hashing():
    """Test password hashing and verification."""
    password = "testpassword"
    hashed_password = get_password_hash(password)
    
    assert hashed_password is not None
    assert isinstance(hashed_password, str)
    assert verify_password(password, hashed_password)
    assert not verify_password("wrongpassword", hashed_password)

def test_jwt_creation_and_decoding():
    """Test JWT creation and decoding."""
    username = "testuser"
    # Test with a standard expiration
    token = create_access_token(data={"sub": username})
    decoded_data = decode_access_token(token)
    assert decoded_data.username == username

    # Test with a custom expiration
    expires = timedelta(minutes=5)
    token_with_custom_expiry = create_access_token(data={"sub": username}, expires_delta=expires)
    decoded_data_custom = decode_access_token(token_with_custom_expiry)
    assert decoded_data_custom.username == username

    # Test with an invalid token
    invalid_token = "this.is.an.invalid.token"
    assert decode_access_token(invalid_token) is None

# --- Tests for core/database.py ---

# Setup an in-memory SQLite database for testing
@pytest.fixture(scope="module")
def test_db_session():
    """Fixture to create a temporary in-memory SQLite database for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_user_model(test_db_session):
    """Test creating a user and adding it to the database."""
    db = test_db_session
    username = "testuser_db"
    password = "testpassword"
    hashed_password = get_password_hash(password)
    
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    user_in_db = db.query(User).filter(User.username == username).first()
    
    assert user_in_db is not None
    assert user_in_db.username == username
    assert user_in_db.hashed_password == hashed_password

def test_get_db_dependency():
    """Test the get_db dependency provider."""
    # This is more of an integration test, but we can check if it yields a session
    db_generator = get_db()
    db_session = next(db_generator)
    assert db_session is not None
    try:
        # The generator should close the session in the finally block
        next(db_generator)
    except StopIteration:
        pass
    
    # After the generator is exhausted, the session should be closed.
    # A direct way to check this is difficult without inspecting internal state,
    # but we can assert that the generator is exhausted.
    with pytest.raises(StopIteration):
        next(db_generator)
