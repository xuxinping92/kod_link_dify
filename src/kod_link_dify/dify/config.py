"""
Dify 客户端配置
"""
import os

# ==============================
# 基础配置（可用环境变量覆盖）
# ==============================

# Dify 部署地址（不要以 / 结尾）
base_url: str = os.getenv("DIFY_BASE_URL", "https://ai.wxskii.cn")

# 知识库 API Key（Dataset API Key）
# ⚠️ 强烈建议通过环境变量 DIFY_API_KEY 设置，不要把密钥写进代码仓库
api_key: str = os.getenv("DIFY_API_KEY", "dataset-0SnuPlm7UjplA2BtbzZVJC2q")

# 请求超时时间（秒）
request_timeout: int = int(os.getenv("DIFY_TIMEOUT", "30"))

# 调试模式（打印更多日志）
debug: bool = os.getenv("DIFY_DEBUG", "false").lower() == "true"