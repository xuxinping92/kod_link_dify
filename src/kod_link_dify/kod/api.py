import requests

from .config import base_url, password, request_timeout, username


class KodClient:
    def __init__(
        self,
        base_url: str = base_url,
        username: str = username,
        password: str = password,
    ):
        self.base: str = base_url.rstrip("/")
        self.username: str = username
        self.password: str = password
        self.session = requests.Session()
        self.token = None

    def login(self) -> str:
        """登录可道云，保存 token"""
        url = f"{self.base}/?user/index/loginSubmit&name={self.username}&password={self.password}"
        r = self.session.get(url)
        j: dict = r.json()
        if j.get("code") and "info" in j:
            self.token: str = j["info"]
            print("可道云登录成功，获取到 token")
            return self.token
        else:
            raise ValueError("可道云登录失败，未返回 token")

    def get_options(
        self,
        token: str | None = None,
        timeout: int = request_timeout,
    ) -> dict:
        """
        获取系统配置信息
        token: 可道云的 accessToken，默认为 None（自动获取）
        timeout: 请求超时时间，默认使用配置中的 request_timeout

        返回值：字典，包含配置信息
        """
        if token is None:
            if self.token is None:
                raise ValueError("请先调用 login() 登录获取 token")
            token = self.token  # 自动获取

        url = f"{self.base}/index.php?user/view/options&accessToken={token}"
        resp = self.session.get(url, timeout=timeout)
        resp.raise_for_status()

        try:
            return resp.json()
        except ValueError:
            # 避免 JSON 解析失败时无提示
            return {"raw": resp.text}

    def list_dir(self, path: str = "io_/"):
        """
        列出目录下的文件和文件夹
        :param path: Kod 内部路径，例如 'io_/' 表示根目录
        :return: list，每个元素是一个 dict（包含 name、path、type 等）
        """
        if not self.token:
            raise ValueError("请先调用 login() 登录获取 token")

        url = f"{self.base}/?explorer/list/path&path={path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        r = self.session.get(url, headers=headers)

        if r.status_code != 200:
            raise RuntimeError(f"请求失败: {r.status_code}, {r.text}")

        j: dict = r.json()
        if not j.get("code"):
            raise RuntimeError(f"获取目录失败: {j}")

        return j.get("data", [])

    def get_file_info(self, file_path: str):
        """
        获取指定文件的元信息
        :param file_path: 可道云中的文件路径，例如 '/home/xxu/test/test1.txt'
        :return: dict (包含文件信息)
        """
        if not self.token:
            raise ValueError("请先调用 login() 登录获取 token")

        # API 地址: explorer/index/pathInfo
        url = f"{self.base}/?explorer/index/pathInfo&path={file_path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        r = self.session.get(url, headers=headers)

        if r.status_code != 200:
            raise RuntimeError(f"请求失败: {r.status_code}, {r.text}")

        j: dict = r.json()
        if not j.get("code"):
            raise RuntimeError(f"获取文件信息失败: {j}")

        return j.get("data")  # 返回 data 部分，一般包含 name、size、mtime 等字段
