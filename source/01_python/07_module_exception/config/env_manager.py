# config/env_manager.py
# 环境变量管理：加载 .env 文件、读取和验证配置
#
# 依赖关系（包内导入）：
#   - config.exceptions → ConfigError（配置缺失时抛出）
#   - config.enums → ModelProvider（模型选择枚举）

import os
from dotenv import load_dotenv

from config.exceptions import ConfigError
from config.enums import ModelProvider


def load_env(env_file: str = ".env") -> bool:
    """
    加载 .env 文件

    Args:
        env_file: .env 文件路径，默认为当前目录的 .env

    Returns:
        是否成功加载
    """
    loaded = load_dotenv(env_file, override=True)
    if loaded:
        print(f"✅ 已加载环境变量文件: {env_file}")
    else:
        print(f"⚠️  未找到环境变量文件: {env_file}（将使用系统环境变量或默认值）")
    return loaded


def get_env(key: str, default: str | None = None, required: bool = False) -> str | None:
    """
    获取环境变量

    Args:
        key: 环境变量名
        default: 默认值
        required: 是否必须存在

    Returns:
        环境变量值

    Raises:
        ConfigError: 当 required=True 且变量不存在时
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ConfigError(key)
    return value


def get_config() -> dict:
    """
    加载并返回完整的应用配置

    Returns:
        包含所有配置项的字典

    Raises:
        ConfigError: 缺少必要配置时
    """
    load_env()

    api_key = get_env("OPENAI_API_KEY", required=True)

    model_name = get_env("MODEL_NAME", default="gpt-4o-mini")
    temperature = float(get_env("TEMPERATURE", default="0.7"))
    debug = get_env("DEBUG", default="false").lower() == "true"

    provider_str = get_env("MODEL_PROVIDER", default="openai")
    try:
        provider = ModelProvider(provider_str)
    except ValueError:
        valid = [p.value for p in ModelProvider]
        raise ConfigError(
            "MODEL_PROVIDER",
            f"无效的 MODEL_PROVIDER: '{provider_str}'，可选值: {valid}"
        )

    return {
        "api_key": api_key,
        "model": model_name,
        "temperature": temperature,
        "debug": debug,
        "provider": provider,
        "api_base_url": provider.get_api_base_url(),
    }


def print_config(config: dict) -> None:
    """打印配置（隐藏敏感信息）"""
    print("\n📋 当前配置：")
    for key, value in config.items():
        if "key" in key.lower() or "secret" in key.lower():
            display = f"{str(value)[:8]}...（已隐藏）" if value else "未设置"
        else:
            display = value
        print(f"  {key}: {display}")


if __name__ == "__main__":
    print("=== 环境变量管理测试 ===\n")

    # 测试加载配置
    try:
        config = get_config()
        print_config(config)
    except ConfigError as e:
        print(f"\n❌ 配置错误: {e}")
        print("请复制 .env.example 为 .env 并填入真实配置")

    # 测试必要变量缺失
    print("\n\n=== 测试必要变量缺失 ===")
    try:
        get_env("NON_EXISTENT_KEY", required=True)
    except ConfigError as e:
        print(f"✅ 正确捕获: {e}")
