# config 包
# 统一导出配置相关的模块内容，简化外部导入路径
#
# 使用方式：
#   from config import AppError, ConfigError       （异常）
#   from config import TaskStatus, ModelProvider    （枚举）
#   from config import get_config, load_env         （配置管理，需要 python-dotenv）

from config.exceptions import AppError, ConfigError, CalculationError
from config.enums import TaskStatus, ModelProvider

try:
    from config.env_manager import get_config, load_env
except ImportError:
    # python-dotenv 未安装时，env_manager 不可用，其余功能正常
    get_config = None  # type: ignore
    load_env = None  # type: ignore
