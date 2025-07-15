import argparse
import logging
from sqlalchemy.orm import Session
from core.database import SessionLocal, User
from core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_user(db: Session, username: str, password: str):
    """Creates a new user in the database."""
    # Ensure tables are created
    from core.database import create_db_and_tables
    create_db_and_tables()
    
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        logger.warning(f"User '{username}' already exists.")
        return
    
    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"Successfully created user: {new_user.username}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new user for the MCP application.")
    parser.add_argument("--username", type=str, required=True, help="The username for the new user.")
    parser.add_argument("--password", type=str, required=True, help="The password for the new user.")
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        create_user(db, username=args.username, password=args.password)
    finally:
        db.close()
