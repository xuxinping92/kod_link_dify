import requests
from .auth import get_token
from .config import base_url, request_timeout

def get_options(token: str | None = None, timeout: int = request_timeout) -> dict:
    """
    获取系统配置信息
    token: 可道云的 accessToken，默认为 None（自动获取）
    timeout: 请求超时时间，默认使用配置中的 request_timeout
    
    返回值：字典，包含配置信息
    """
    if token is None:
        token = get_token()  # 自动获取

    url = f"{base_url}/index.php?user/view/options&accessToken={token}"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()

    try:
        return resp.json()
    except ValueError:
        # 避免 JSON 解析失败时无提示
        return {"raw": resp.text}