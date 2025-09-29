"""
项目配置文件
"""

import os

# ==============================
# 基础配置
# ==============================

# 服务地址
base_url: str = os.getenv("KOD_BASE_URL", "http://186.10.0.23")

# 用户名
username: str = os.getenv("KOD_USERNAME", "许鑫平")

# 密码（⚠️ 建议在生产环境用环境变量传递，不要写死）
password: str = os.getenv("KOD_PASSWORD", "wuxin1234")

# ==============================
# 其他可扩展配置
# ==============================

# 请求超时时间（秒）
request_timeout: int = int(os.getenv("KOD_TIMEOUT", "10"))

# 是否启用调试模式
debug: bool = os.getenv("KOD_DEBUG", "false").lower() == "true"