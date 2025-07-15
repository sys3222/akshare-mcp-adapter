from datetime import timedelta
from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, Query, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import json

from models.schemas import (
    BacktestResult, PaginatedDataResponse, Token, UserInDB,
    LLMAnalysisRequest, LLMAnalysisResponse
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

# --- LLM Intelligent Analysis ---

@router.post("/llm/analyze", response_model=LLMAnalysisResponse, tags=["LLM Analysis"])
async def llm_intelligent_analysis(
    request: LLMAnalysisRequest,
    use_llm: bool = True,
    current_user: User = Depends(get_current_active_user)
) -> LLMAnalysisResponse:
    """
    LLM智能分析接口

    支持两种分析模式：
    1. LLM模式 (use_llm=True): 使用Gemini模型进行智能分析，支持自动工具调用
    2. 规则模式 (use_llm=False): 使用基于规则的本地分析，快速响应

    支持的查询类型：
    - 股票分析：分析000001、平安银行怎么样
    - 市场概览：今日市场表现如何、大盘情况
    - 财务指标：000001的PE、PB如何
    - 趋势分析：000001未来走势预测
    - 对比分析：000001 vs 600519哪个更好
    - 投资建议：推荐一些股票
    - 风险评估：000001投资风险如何

    参数：
    - use_llm: 是否使用LLM模式（默认True）
    """
    try:
        # 导入LLM处理器
        from handlers.llm_handler import llm_analysis_handler, rule_based_handler

        # 根据参数选择分析器
        handler = llm_analysis_handler if use_llm else rule_based_handler

        # 执行智能分析
        analysis_result = await handler.analyze_query(
            query=request.query,
            username=current_user.username
        )

        # 构建响应
        return LLMAnalysisResponse(
            summary=analysis_result.summary,
            insights=analysis_result.insights,
            recommendations=analysis_result.recommendations,
            data_points=analysis_result.data_points,
            charts_suggested=analysis_result.charts_suggested,
            risk_level=analysis_result.risk_level,
            confidence=analysis_result.confidence,
            intent_detected=analysis_result.confidence > 0.5 and hasattr(llm_analysis_handler, '_last_context')
                           and llm_analysis_handler._last_context
                           and llm_analysis_handler._last_context.intent.value or "unknown",
            entities_extracted=analysis_result.data_points
        )

    except Exception as e:
        logger.error(f"LLM分析失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"智能分析过程中出现错误: {str(e)}"
        )

@router.get("/llm/capabilities", tags=["LLM Analysis"])
async def get_llm_capabilities(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取LLM分析能力说明
    """
    return {
        "supported_intents": [
            {
                "type": "stock_analysis",
                "name": "股票分析",
                "description": "分析特定股票的价格走势、技术指标等",
                "examples": ["分析000001", "平安银行怎么样", "000001表现如何"]
            },
            {
                "type": "market_overview",
                "name": "市场概览",
                "description": "分析整体市场表现和情绪",
                "examples": ["今日市场表现", "大盘情况", "市场概况"]
            },
            {
                "type": "financial_metrics",
                "name": "财务指标",
                "description": "分析财务指标如PE、PB、ROE等",
                "examples": ["000001的PE如何", "财务指标分析", "市盈率情况"]
            },
            {
                "type": "trend_analysis",
                "name": "趋势分析",
                "description": "分析价格趋势和技术走势",
                "examples": ["000001走势分析", "未来趋势预测", "技术分析"]
            },
            {
                "type": "comparison",
                "name": "对比分析",
                "description": "对比多个股票的表现",
                "examples": ["000001 vs 600519", "对比分析", "哪个更好"]
            },
            {
                "type": "recommendation",
                "name": "投资建议",
                "description": "提供投资建议和推荐",
                "examples": ["推荐股票", "投资建议", "买入建议"]
            },
            {
                "type": "risk_assessment",
                "name": "风险评估",
                "description": "评估投资风险等级",
                "examples": ["000001风险如何", "投资风险评估", "安全吗"]
            }
        ],
        "supported_entities": [
            "股票代码（6位数字）",
            "股票名称",
            "时间范围（最近N天、N个月等）",
            "财务指标名称"
        ],
        "analysis_features": [
            "意图识别和理解",
            "实体提取",
            "数据自动获取",
            "智能分析和洞察",
            "风险评估",
            "投资建议生成",
            "图表建议"
        ],
        "risk_levels": ["低风险", "中等风险", "高风险"],
        "confidence_range": [0.0, 1.0]
    }

@router.post("/llm/chat", tags=["LLM Analysis"])
async def llm_chat_completions(
    prompt: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    简化的LLM聊天接口（借鉴旧版本的优秀设计）

    直接与LLM对话，支持自动工具调用和数据获取
    适合需要更自然对话体验的场景

    参数：
    - prompt: 用户的自然语言查询

    返回：
    - response: LLM的直接回复文本
    """
    try:
        from handlers.llm_handler import llm_analysis_handler

        if not llm_analysis_handler.use_llm:
            raise HTTPException(
                status_code=503,
                detail="LLM功能不可用，请检查GEMINI_API_KEY配置"
            )

        # 使用增强的LLM分析
        analysis_result = await llm_analysis_handler.analyze_query(
            query=prompt,
            username=current_user.username
        )

        # 返回更自然的聊天响应
        return {
            "response": analysis_result.summary,
            "insights": analysis_result.insights,
            "recommendations": analysis_result.recommendations,
            "risk_level": analysis_result.risk_level,
            "confidence": analysis_result.confidence
        }

    except Exception as e:
        logger.error(f"LLM聊天失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"聊天服务出现错误: {str(e)}"
        )
