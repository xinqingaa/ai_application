# utils 包
# 统一导出工具函数，简化外部导入路径
#
# 使用方式：
#   from utils import add, subtract, multiply, divide   （计算器）
#   from utils import save_json, load_json              （JSON 工具）
#   from utils import format_datetime, time_ago          （日期时间工具）

from utils.calculator import add, subtract, multiply, divide
from utils.json_helper import save_json, load_json
from utils.datetime_helper import format_datetime, time_ago, get_timestamp
