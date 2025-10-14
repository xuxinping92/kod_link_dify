import os
from pathlib import Path
from typing import Optional, Union
from urllib.parse import unquote, urlencode

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
        self.token: str | None = None  # accessToken

    def login(self) -> str:
        """
        登录可道云，获取 accessToken
        返回值：token 字符串
        异常：登录失败时抛出 ValueError
        """
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

    def get_doc_permission_list(self) -> dict:
        """
        19.2 文档权限列表获取
        说明：展示已存在的文档权限列表，包含权限角色及对应权限信息，
        可用于表格展示，获取后可本地缓存复用。

        请求地址：
            GET {base}/index.php?admin/auth/get

        返回：
            返回接口的 data 字段（通常为包含角色与权限项的结构化字典/列表）
        异常：
            - 若未登录/无 token：ValueError
            - 请求失败或返回 code != True：RuntimeError
        """
        if not self.token:
            # 若还没登录，这里可以选择自动登录；如果你不想自动登录，改为 raise ValueError
            self.login()
            if not self.token:
                raise ValueError("尚未登录，无法获取文档权限列表（缺少 accessToken）")

        url = f"{self.base}/index.php"
        # 同时在 header 与 query param 里带上 accessToken，兼容不同部署
        headers = {"accessToken": self.token}
        params = {
            "admin/auth/get": "",  # 兼容可道云的 index.php?admin/auth/get 路由风格
            "accessToken": self.token,
        }

        r = self.session.get(url, headers=headers, params=params)
        # 若返回非 2xx，会抛异常更清晰
        r.raise_for_status()

        try:
            j = r.json()
        except Exception as e:
            raise RuntimeError(f"获取文档权限列表失败，返回非 JSON：{r.text[:200]}") from e

        # 典型返回：{"code": True, "data": {...}, "info": "success", ...}
        if isinstance(j, dict) and j.get("code") in (True, 1):
            if "data" in j:
                return j["data"]
            # 有些版本把结果放在 info 或直接放顶层，做个兜底
            if "info" in j and isinstance(j["info"], (dict, list)):
                return j["info"]
            return j  # 兜底返回原对象，避免信息丢失
        else:
            raise RuntimeError(f"获取文档权限列表失败：{j}")

    def download_file(
        self,
        path: str,
        save_to: Optional[Union[str, os.PathLike]] = None,
        overwrite: bool = False,
        chunk_size: int = 1024 * 1024,
        timeout: int = request_timeout,
        extra_params: Optional[dict] = None,
    ) -> Path:
        """
        从 Kod 下载文件到本地。

        Parameters
        ----------
        path : str
            Kod 的 path 参数，例如 "{source:1031}/" 或者 "分享/项目A/报告.pdf" 等。
            按接口要求原样传入（无需手动 urlencode）。
        save_to : str | Path | None
            保存位置。如果是目录，则用远端文件名保存到该目录；
            如果是文件路径，则直接保存到该文件；
            如果为 None，默认保存到当前工作目录下，文件名来自响应头或 path 推断。
        overwrite : bool
            目标文件已存在时是否覆盖。
        chunk_size : int
            流式下载的块大小（字节）。
        timeout : int | None
            请求超时；默认使用 client 初始化时的 timeout。
        extra_params : dict | None
            额外 query 参数，通常不需要。

        Returns
        -------
        pathlib.Path
            实际保存的本地文件路径。

        Raises
        ------
        requests.HTTPError
            当 HTTP 状态码非 2xx。
        FileExistsError
            当目标文件已存在且 overwrite=False。
        RuntimeError
            当无法确定保存文件名时。
        """
        # 组合为 "?explorer/index/fileOut&path=...&download=1"
        query = {"path": path, "download": 1}
        if extra_params:
            query.update(extra_params)

        # 手动拼装，确保与 Kod 的“动作式”路径保持一致
        # 最终效果: http://host/index.php?explorer/index/fileOut&path=...&download=1
        query_string = "?" + "&".join(
            ["explorer/index/fileOut"] + [urlencode({k: v}) for k, v in query.items()]
        )
        full_url = f"{self.base}/index.php{query_string}"

        # 发起流式下载
        resp = self.session.get(full_url, stream=True, timeout=timeout)
        resp.raise_for_status()

        # 从 Content-Disposition 中解析文件名
        filename = None
        cd = resp.headers.get("Content-Disposition") or resp.headers.get("content-disposition")
        if cd:
            # 兼容 filename* 与 filename
            # 例: attachment; filename="报告.pdf"
            # 或: attachment; filename*=UTF-8''%E6%8A%A5%E5%91%8A.pdf
            parts = [p.strip() for p in cd.split(";")]
            for p in parts:
                if p.lower().startswith("filename*="):
                    # RFC 5987: filename*=UTF-8''urlencoded
                    try:
                        enc_and_name = p.split("=", 1)[1]
                        _, _, enc_name = enc_and_name.partition("''")
                        filename = unquote(enc_name.strip().strip('"'))
                        break
                    except Exception:
                        pass
                if p.lower().startswith("filename=") and filename is None:
                    val = p.split("=", 1)[1].strip().strip('"')
                    filename = unquote(val)

        # 兜底：若无法从响应头得到文件名，尝试从 path 推断
        if not filename:
            # 去掉末尾的 '/'，取最后一段
            guess = path.rstrip("/").split("/")[-1]
            # 如果是像 {source:1031} 这种占位，给个通用名
            if guess.startswith("{") and guess.endswith("}"):
                guess = "download.bin"
            filename = guess or "download.bin"

        # 计算最终保存路径
        if save_to is None:
            target = Path.cwd() / filename
        else:
            save_to = Path(save_to)
            if save_to.exists() and save_to.is_dir():
                target = save_to / filename
            elif save_to.suffix:  # 显式文件路径
                target = save_to
            else:
                # 目标目录（不存在则创建）
                save_to.mkdir(parents=True, exist_ok=True)
                target = save_to / filename

        if target.exists() and not overwrite:
            raise FileExistsError(
                f"Target file exists: {target}. Set overwrite=True to replace it."
            )

        # 写入文件
        with open(target, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)

        return target
