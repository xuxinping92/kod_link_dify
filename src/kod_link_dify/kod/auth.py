import requests
from .config import base_url, username, password, request_timeout

def get_token(
    user: str = username,
    pwd: str = password,
    base: str = base_url,
    timeout: int = request_timeout,
) -> str:
    """
    登录并返回 token
    
    user: 用户名
    pwd: 密码
    base: 可道云的基础 URL（不要以 / 结尾）
    timeout: 请求超时时间，默认使用配置中的 request_timeout
    返回值：字符串，accessToken
    """
    s = requests.Session()
    url = f"{base}/?user/index/loginSubmit&name={user}&password={pwd}"
    resp = s.get(url, timeout=timeout)
    resp.raise_for_status()

    try:
        j = resp.json()
    except ValueError:
        raise ValueError(f"登录失败：响应不是 JSON，text={resp.text[:200]}")

    if j.get("code") and "info" in j:
        return j["info"]

    raise ValueError(f"登录失败: {j}")