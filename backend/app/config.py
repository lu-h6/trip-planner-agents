"""Application configuration.

The project is normally started from the repository root, but configuration
should not depend on the caller's current working directory.
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

# BaseAgent reads several values directly from os.environ, so load the same
# repository-level .env before any application services are initialized.
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基本配置
    app_name: str = "BaseAgent智能旅行助手"
    app_version: str = "0.1.0"
    debug: bool = False
    reload: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS配置 - 使用字符串,在代码中分割
    cors_origins: str = (
        "http://localhost:5173,http://localhost:3000,"
        "http://127.0.0.1:5173,http://127.0.0.1:3000"
    )

    # 高德地图API配置
    amap_api_key: str = ""

    # Unsplash API配置
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    # LLM配置 (BaseAgent也会直接读取这些环境变量)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model_id: str = ""
    llm_timeout: int = 60

    # 日志配置
    log_level: str = "INFO"

    # 本地记忆存储目录
    memory_data_dir: Path = PROJECT_ROOT / "backend" / "memory_data"

    def get_cors_origins_list(self) -> List[str]:
        """获取CORS origins列表"""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def get_memory_data_dir(self) -> Path:
        """返回解析到仓库根目录的记忆存储目录."""
        if self.memory_data_dir.is_absolute():
            return self.memory_data_dir
        return PROJECT_ROOT / self.memory_data_dir


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


def get_llm_api_key() -> str:
    """获取统一或提供商专用的 LLM API Key."""
    return (
        os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("KIMI_API_KEY")
        or os.getenv("MOONSHOT_API_KEY")
        or os.getenv("ZHIPU_API_KEY")
        or ""
    )


def validate_config():
    """验证必要配置是否完整."""
    errors = []
    warnings = []

    if not settings.amap_api_key:
        errors.append("AMAP_API_KEY未配置")

    if not get_llm_api_key():
        warnings.append("LLM_API_KEY或提供商专用API Key未配置,LLM功能可能无法使用")

    if errors:
        error_msg = "配置错误:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)

    if warnings:
        print("\n[WARN] 配置警告:")
        for warning in warnings:
            print(f"  - {warning}")

    return True


def print_config():
    """打印当前配置(隐藏敏感信息)."""
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print(f"服务器: {settings.host}:{settings.port}")
    print(f"高德地图API Key: {'已配置' if settings.amap_api_key else '未配置'}")

    llm_base_url = os.getenv("LLM_BASE_URL") or settings.llm_base_url
    llm_model = os.getenv("LLM_MODEL_ID") or settings.llm_model_id or "自动选择"

    print(f"LLM API Key: {'已配置' if get_llm_api_key() else '未配置'}")
    print(f"LLM Base URL: {llm_base_url}")
    print(f"LLM Model: {llm_model}")
    print(f"日志级别: {settings.log_level}")
