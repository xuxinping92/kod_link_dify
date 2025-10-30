import os
import urllib.parse
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import unquote, urlencode

import requests

from .config import base_url, password, request_timeout, username


class KodClient:
    def __init__(
        self,
        base_url: str = base_url,
        username: str = username,
        password: str = password,
        timeout: int = request_timeout,
    ):
        self.base: str = base_url.rstrip("/")
        self.username: str = username
        self.password: str = password
        self.session = requests.Session()
        self.timeout: int = timeout
        self.token: str = ""  # 登录后填充

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
        timeout: int = None,
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
        if timeout is None:
            timeout = self.timeout
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

    def _download_one(
        self,
        one_path: str,
        save_to: Optional[Path],
        overwrite: bool = False,
        chunk_size: int = 1024 * 1024,
        timeout: Optional[int] = None,
        extra_params: Optional[dict] = None,
    ) -> Path:
        """下载单个文件"""
        query = {"path": one_path, "download": 1}
        if extra_params:
            query.update(extra_params)

        # 拼接 Kod 动作式 URL
        query_string = "?" + "&".join(
            ["explorer/index/fileOut"] + [urlencode({k: v}) for k, v in query.items()]
        )
        full_url = f"{self.base}/index.php{query_string}"
        _timeout = self.timeout if timeout is None else timeout

        # 发起流式请求
        resp = self.session.get(full_url, stream=True, timeout=_timeout)
        resp.raise_for_status()

        # 解析文件名
        filename = None
        cd = resp.headers.get("Content-Disposition") or resp.headers.get("content-disposition")
        if cd:
            parts = [p.strip() for p in cd.split(";")]
            for p in parts:
                if p.lower().startswith("filename*="):
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

        if not filename:
            guess = one_path.rstrip("/").split("/")[-1]
            if guess.startswith("{") and guess.endswith("}"):
                guess = "download.bin"
            filename = guess or "download.bin"

        # 确定保存路径
        if save_to is None:
            target = Path.cwd() / filename
        else:
            if save_to.exists() and save_to.is_dir():
                target = save_to / filename
            elif save_to.suffix:
                target = save_to
            else:
                save_to.mkdir(parents=True, exist_ok=True)
                target = save_to / filename

        if target.exists() and not overwrite:
            raise FileExistsError(f"Target file exists: {target}")

        # 写入文件
        with open(target, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)

        return target

    def download_file(
        self,
        path: Union[str, List[str]],
        save_to: Optional[Union[str, os.PathLike]] = None,
        overwrite: bool = False,
        chunk_size: int = 1024 * 1024,
        timeout: Optional[int] = None,
        extra_params: Optional[dict] = None,
    ) -> Union[Path, List[Path]]:
        """
        从 Kod 下载单个或多个文件。
        - 传入单个 path: 返回 Path
        - 传入多个 path: 返回 list[Path]
        """
        save_to_path = Path(save_to) if save_to else None

        # 单个文件
        if isinstance(path, str):
            return self._download_one(
                path, save_to_path, overwrite, chunk_size, timeout, extra_params
            )

        # 批量下载
        if not isinstance(path, (list, tuple)):
            raise TypeError("path must be str or list[str]")

        if save_to_path and save_to_path.suffix:
            raise ValueError("When downloading multiple paths, 'save_to' must be a directory")

        base_dir = save_to_path or Path.cwd()
        base_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for p in path:
            results.append(
                self._download_one(p, base_dir, overwrite, chunk_size, timeout, extra_params)
            )

        return results

    def download_folder_files(
        self,
        folder_path: str,
        save_to: Union[str, Path],
        overwrite: bool = False,
        chunk_size: int = 1024 * 1024,
        timeout: Optional[int] = None,
    ) -> List[Path]:
        """
        简单版：
        - 不递归
        - 默认登录已经拿到了 self.token
        - 列目录、下载都同时带上多种 token 名字，兼容老版本 Kod
        """
        timeout = self.timeout if timeout is None else timeout
        save_dir = Path(save_to).expanduser().resolve()
        save_dir.mkdir(parents=True, exist_ok=True)

        # 1) 列目录
        list_url = f"{self.base}/index.php?explorer/list/path"
        token = getattr(self, "token", None)
        payload = {
            "path": folder_path,
        }
        if token:
            # 一次性全带，服务端认哪个用哪个
            payload["CSRF_TOKEN"] = token
            payload["csrfToken"] = token
            payload["accessToken"] = token
            payload["token"] = token

        resp = self.session.post(list_url, data=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        data: dict

        if not data.get("code"):
            # 把服务端说的话打出来，方便你看它到底要哪个字段
            raise RuntimeError(f"list folder failed: {data}")

        # 老 Kod 常见结构：data -> data -> fileList
        file_list = data["data"].get("fileList", [])
        downloaded: List[Path] = []

        for item in file_list:
            item: dict
            # 跳过目录
            if item.get("type") == "folder" or item.get("isFolder") == 1:
                continue

            remote_path = item.get("path")
            if not remote_path:
                continue

            filename = item.get("name") or "unnamed"
            local_path = save_dir / filename
            if local_path.exists() and not overwrite:
                downloaded.append(local_path)
                continue

            # 2) 下载文件
            safe_path = urllib.parse.quote(remote_path, safe="")
            # 拼一个最全的版本
            dl_url = (
                f"{self.base}/index.php?explorer/index/fileOut" f"&path={safe_path}" f"&download=1"
            )
            if token:
                dl_url += (
                    f"&CSRF_TOKEN={token}"
                    f"&csrfToken={token}"
                    f"&accessToken={token}"
                    f"&token={token}"
                )

            with self.session.get(dl_url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)

            downloaded.append(local_path)

        return downloaded
