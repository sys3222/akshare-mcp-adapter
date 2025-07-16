"""
配置管理模块
统一管理应用程序的所有配置项
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///./akshare_mcp.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20

@dataclass
class SecurityConfig:
    """安全配置"""
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    password_min_length: int = 8

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "gemini"  # gemini, openai, etc.
    model_name: str = "gemini-1.5-pro-latest"
    api_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    fallback_to_rules: bool = True

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl_seconds: int = 3600  # 1小时
    max_size: int = 1000
    cleanup_interval: int = 300  # 5分钟

@dataclass
class APIConfig:
    """API配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list = None
    rate_limit_per_minute: int = 60
    max_request_size: int = 10 * 1024 * 1024  # 10MB

@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class TestConfig:
    """测试配置"""
    enabled: bool = True
    mock_llm: bool = True
    test_data_path: str = "tests/data"
    coverage_threshold: float = 0.8

@dataclass
class AppConfig:
    """应用程序主配置"""
    environment: str = "development"  # development, production, testing
    debug: bool = True
    version: str = "1.0.0"
    
    # 子配置
    database: DatabaseConfig = None
    security: SecurityConfig = None
    llm: LLMConfig = None
    cache: CacheConfig = None
    api: APIConfig = None
    logging: LoggingConfig = None
    test: TestConfig = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.database is None:
            self.database = DatabaseConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.llm is None:
            self.llm = LLMConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.api is None:
            self.api = APIConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.test is None:
            self.test = TestConfig()

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self._config: Optional[AppConfig] = None
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        try:
            # 首先加载默认配置
            self._config = AppConfig()
            
            # 尝试从文件加载配置
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self._merge_config(config_data)
            
            # 从环境变量覆盖配置
            self._load_from_env()
            
            logger.info(f"配置加载完成，环境: {self._config.environment}")
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            # 使用默认配置
            self._config = AppConfig()
    
    def _merge_config(self, config_data: Dict[str, Any]):
        """合并配置数据"""
        for key, value in config_data.items():
            if hasattr(self._config, key):
                if isinstance(value, dict):
                    # 递归合并子配置
                    sub_config = getattr(self._config, key)
                    if sub_config:
                        for sub_key, sub_value in value.items():
                            if hasattr(sub_config, sub_key):
                                setattr(sub_config, sub_key, sub_value)
                else:
                    setattr(self._config, key, value)
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 通用环境变量
        if os.getenv("ENVIRONMENT"):
            self._config.environment = os.getenv("ENVIRONMENT")
        if os.getenv("DEBUG"):
            self._config.debug = os.getenv("DEBUG").lower() == "true"
        
        # LLM配置
        if os.getenv("GEMINI_API_KEY"):
            self._config.llm.api_key = os.getenv("GEMINI_API_KEY")
        if os.getenv("LLM_MODEL"):
            self._config.llm.model_name = os.getenv("LLM_MODEL")
        
        # 数据库配置
        if os.getenv("DATABASE_URL"):
            self._config.database.url = os.getenv("DATABASE_URL")
        
        # 安全配置
        if os.getenv("SECRET_KEY"):
            self._config.security.secret_key = os.getenv("SECRET_KEY")
        
        # API配置
        if os.getenv("API_HOST"):
            self._config.api.host = os.getenv("API_HOST")
        if os.getenv("API_PORT"):
            self._config.api.port = int(os.getenv("API_PORT"))
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config_dict = asdict(self._config)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到 {self.config_file}")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
    
    def get_config(self) -> AppConfig:
        """获取配置"""
        return self._config
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self._config.environment == "production"
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self._config.environment == "development"
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self._config.environment == "testing"

# 全局配置管理器实例
config_manager = ConfigManager()

def get_config() -> AppConfig:
    """获取全局配置"""
    return config_manager.get_config()

def get_llm_config() -> LLMConfig:
    """获取LLM配置"""
    return config_manager.get_config().llm

def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    return config_manager.get_config().database

def get_security_config() -> SecurityConfig:
    """获取安全配置"""
    return config_manager.get_config().security

def get_api_config() -> APIConfig:
    """获取API配置"""
    return config_manager.get_config().api

def get_cache_config() -> CacheConfig:
    """获取缓存配置"""
    return config_manager.get_config().cache

def get_logging_config() -> LoggingConfig:
    """获取日志配置"""
    return config_manager.get_config().logging

def get_test_config() -> TestConfig:
    """获取测试配置"""
    return config_manager.get_config().test

# 配置验证函数
def validate_config() -> bool:
    """验证配置的有效性"""
    config = get_config()
    errors = []
    
    # 验证LLM配置
    if config.llm.provider == "gemini" and not config.llm.api_key:
        errors.append("Gemini API密钥未配置")
    
    # 验证安全配置
    if len(config.security.secret_key) < 32:
        errors.append("安全密钥长度不足")
    
    # 验证数据库配置
    if not config.database.url:
        errors.append("数据库URL未配置")
    
    if errors:
        logger.error(f"配置验证失败: {', '.join(errors)}")
        return False
    
    logger.info("配置验证通过")
    return True

def setup_logging():
    """根据配置设置日志"""
    log_config = get_logging_config()
    
    # 创建日志目录
    if log_config.file_path:
        log_dir = Path(log_config.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, log_config.level.upper()),
        format=log_config.format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_config.file_path) if log_config.file_path else logging.NullHandler()
        ]
    )
    
    logger.info("日志系统初始化完成")
