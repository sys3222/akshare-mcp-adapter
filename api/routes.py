from datetime import timedelta
from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, Query, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from models.schemas import (
    BacktestResult, DataSourceList, AkShareCodeRequest, AkShareCodeResponse,
    PaginatedDataResponse, Token, UserInDB
)
from core.mcp_protocol import MCPRequest
from core import security
from core.database import get_db, User
from handlers.backtest_handler import (
    handle_upload_and_run_backtest,
    handle_backtest_with_code_only,
    handle_backtest_with_mcp_data
)
from handlers.data_source_handler import handle_get_data_sources
from handlers.akshare_handler import handle_execute_akshare_code
from handlers.mcp_handler import handle_mcp_data_request

router = APIRouter()

# --- Authentication ---

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = db.query(User).filter(User.username == username).first()
    if not user or not security.verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_active_user(
    token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Dependency to get the current active user."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = security.decode_access_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Login and get an access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserInDB, tags=["Authentication"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current logged in user."""
    return current_user

# --- Backtesting ---
# Note: For simplicity, these are not protected yet. They can be protected by adding
# current_user: User = Depends(get_current_active_user) to their signatures.

@router.post("/backtest", response_model=BacktestResult, tags=["Backtesting"])
async def upload_and_run_backtest(
    strategy_file: UploadFile = File(...),
    data_file: Optional[UploadFile] = File(None),
    params: Optional[str] = Form(None),
    data_source: Optional[str] = Form(None),
    benchmark_symbol: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload strategy and data files to run a backtest. **Requires authentication.**
    """
    return await handle_upload_and_run_backtest(
        strategy_file, data_file, params, data_source, benchmark_symbol
    )

@router.post("/backtest-with-mcp", response_model=BacktestResult, tags=["Backtesting"])
async def backtest_with_mcp_data(
    strategy_file: UploadFile = File(...),
    interface: str = Form(...),
    symbol: str = Form(...),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    params: Optional[str] = Form(None),
    benchmark_symbol: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Run a backtest using data fetched directly via an AkShare interface. **Requires authentication.**
    """
    return await handle_backtest_with_mcp_data(
        strategy_file, interface, symbol, start_date, end_date, params, benchmark_symbol
    )

# --- Data Sources ---

@router.get("/data-sources", response_model=DataSourceList, tags=["Data Sources"])
async def get_data_sources():
    return handle_get_data_sources()

# --- MCP Data (Protected) ---

@router.post("/mcp-data", response_model=PaginatedDataResponse, tags=["MCP Protocol"])
async def get_mcp_data(
    request: MCPRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get paginated data from AkShare. **Requires authentication.**
    """
    return await handle_mcp_data_request(
        request, page, page_size, current_user.username
    )

import json

# ... (existing code) ...

@router.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok"}

@router.get("/interfaces", tags=["System"])
def get_interfaces_config():
    """
    Get the list of available AkShare interfaces from the config file.
    """
    try:
        with open("akshare_interfaces.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Interface configuration file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading interface configuration: {e}")

