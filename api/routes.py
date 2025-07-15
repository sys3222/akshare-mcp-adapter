from datetime import timedelta
from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, Query, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import json

from models.schemas import (
    BacktestResult, PaginatedDataResponse, Token, UserInDB
)
from core.mcp_protocol import MCPRequest
from core import security
from core.database import get_db, User
from handlers.backtest_handler import handle_backtest_with_mcp_data
from handlers.mcp_handler import handle_mcp_data_request
from handlers.data_exploration_handler import handle_explore_data_from_file
from handlers.file_management_handler import (
    save_uploaded_file, list_user_files, delete_user_file, get_user_file_path
)

router = APIRouter()

# --- Authentication ---

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user or not security.verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_active_user(
    token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)
) -> User:
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
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserInDB, tags=["Authentication"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# --- Backtesting ---

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
    return await handle_backtest_with_mcp_data(
        strategy_file, interface, symbol, start_date, end_date, params, benchmark_symbol
    )

# --- Data Fetching & Management ---

@router.post("/mcp-data", response_model=PaginatedDataResponse, tags=["Data Fetching"])
async def get_mcp_data(
    request: MCPRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    return await handle_mcp_data_request(
        request, page, page_size, current_user.username
    )

@router.post("/data/upload", tags=["Data Management"])
async def upload_data_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    return await save_uploaded_file(file, current_user.username)

@router.get("/data/files", response_model=List[str], tags=["Data Management"])
async def get_user_files(current_user: User = Depends(get_current_active_user)):
    return list_user_files(current_user.username)

@router.delete("/data/files/{filename}", tags=["Data Management"])
async def remove_user_file(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    return delete_user_file(filename, current_user.username)

@router.post("/data/explore/{filename}", response_model=PaginatedDataResponse, tags=["Data Exploration"])
async def explore_data_from_file_route(
    filename: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    file_path = get_user_file_path(filename, current_user.username)
    return await handle_explore_data_from_file(file_path, page, page_size)

# --- System ---

@router.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok"}

@router.get("/interfaces", tags=["System"])
def get_interfaces_config():
    try:
        with open("akshare_interfaces.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Interface configuration file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading interface configuration: {e}")

@router.get("/cache/status", tags=["System"])
async def get_cache_status(current_user: User = Depends(get_current_active_user)):
    """获取缓存状态信息"""
    try:
        from pathlib import Path
        import os
        from datetime import datetime

        cache_dir = Path("static/cache/system")
        cache_info = {
            "cache_directory": str(cache_dir),
            "total_files": 0,
            "total_size_mb": 0,
            "files": []
        }

        if cache_dir.exists():
            for cache_file in cache_dir.glob("*.parquet"):
                file_stat = cache_file.stat()
                file_info = {
                    "filename": cache_file.name,
                    "size_mb": round(file_stat.st_size / 1024 / 1024, 2),
                    "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "age_hours": round((datetime.now().timestamp() - file_stat.st_mtime) / 3600, 1)
                }
                cache_info["files"].append(file_info)
                cache_info["total_size_mb"] += file_info["size_mb"]
                cache_info["total_files"] += 1

        cache_info["total_size_mb"] = round(cache_info["total_size_mb"], 2)
        cache_info["files"] = sorted(cache_info["files"], key=lambda x: x["modified_time"], reverse=True)

        return cache_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {e}")
