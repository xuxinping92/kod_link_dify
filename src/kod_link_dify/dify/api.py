import json
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

from .config import api_key, base_url, request_timeout


class DifyClient:
    """
    Dify 知识库（Datasets）API 封装
    """

    def __init__(
        self,
        base_url: str = base_url,
        api_key: str = api_key,
        timeout: int = request_timeout,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base = base_url.rstrip("/")
        self.session = session or requests.Session()
        if not api_key:
            # 允许无密钥初始化，但调用时会 401；这里仅做提醒，不抛错
            pass
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        self.timeout = timeout

    # ========== Datasets ==========

    def list_datasets(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """知识库列表（分页）
        GET /v1/datasets?page=1&limit=20
        文档出处：“知识库列表”段落
        """
        url = f"{self.base}/v1/datasets"
        r = self.session.get(url, params={"page": page, "limit": limit}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ========== Documents ==========

    def list_documents(self, dataset_id: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """某知识库内的文档列表
        GET /v1/datasets/{dataset_id}/documents
        文档出处：“知识库文档列表”段落
        """
        url = f"{self.base}/v1/datasets/{dataset_id}/documents"
        r = self.session.get(url, params={"page": page, "limit": limit}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def upload_document_file(
        self,
        dataset_id: str,
        file_path: str,
        *,
        name: Optional[str] = None,
        indexing_technique: str = "high_quality",
        process_rule: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        使用文件上传方式向指定的知识库（dataset）中创建一个文档（Document）。

        对应 API：POST /v1/datasets/{dataset_id}/document/create-by-file :contentReference[oaicite:1]{index=1}

        参数：
        - dataset_id: 知识库 ID
        - file_path: 本地文件路径
        - name: 上传后的文档名称（如果不传，默认用 file_path 的 basename）
        - indexing_technique: 索引方式，比如 "high_quality" 或其它（以 Dify 支持的为准）
        - process_rule: 可选的处理规则 JSON 对象，按 Dify API 定义格式构造
        - kwargs: 未来扩展参数（例如 “mode” 等）

        返回：
        - API 返回的 JSON（通常包含 document 对象等信息）
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        url = f"{self.base}/v1/datasets/{dataset_id}/document/create-by-file"

        if name is None:
            name = os.path.basename(file_path)

        payload = {
            "name": name,
            "indexing_technique": indexing_technique,
        }
        if process_rule is not None:
            payload["process_rule"] = process_rule
        payload.update(kwargs)

        with open(file_path, "rb") as f:
            files = {
                "data": (None, json.dumps(payload), "application/json"),
                "file": (name, f, "application/octet-stream"),
            }
            resp = self.session.post(url, files=files, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ---------- Internal helpers ----------

    @staticmethod
    def _is_hidden_path(p: str) -> bool:
        name = os.path.basename(p)
        if name.startswith("."):
            return True
        lower = name.lower()
        # 常见系统文件
        return lower in {"thumbs.db", "desktop.ini", "icon\r"}

    def _collect_candidates(
        self,
        folder_path: str,
        *,
        recursive: bool,
        allowed_ext: Optional[List[str]],
        ignore_hidden: bool,
        name_from: str,  # "basename" | "relative"
    ) -> List[Tuple[str, str]]:
        """返回 [(file_path, doc_name), ...]"""
        folder_abs = os.path.abspath(os.path.expanduser(folder_path))
        if not os.path.isdir(folder_abs):
            raise NotADirectoryError(f"Not a directory: {folder_abs}")

        exts = None
        if allowed_ext is not None:
            exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in allowed_ext}

        items: List[Tuple[str, str]] = []

        if recursive:
            for root, dirs, files in os.walk(folder_abs):
                if ignore_hidden:
                    dirs[:] = [d for d in dirs if not self._is_hidden_path(os.path.join(root, d))]
                for fn in files:
                    fp = os.path.join(root, fn)
                    if ignore_hidden and self._is_hidden_path(fp):
                        continue
                    if exts is not None and os.path.splitext(fn)[1].lower() not in exts:
                        continue
                    if not os.path.isfile(fp):
                        continue
                    if name_from == "relative":
                        doc_name = os.path.relpath(fp, start=folder_abs).replace("\\", "/")
                    else:
                        doc_name = os.path.basename(fp)
                    items.append((fp, doc_name))
        else:
            for fn in os.listdir(folder_abs):
                fp = os.path.join(folder_abs, fn)
                if not os.path.isfile(fp):
                    continue
                if ignore_hidden and self._is_hidden_path(fp):
                    continue
                if exts is not None and os.path.splitext(fn)[1].lower() not in exts:
                    continue
                if name_from == "relative":
                    doc_name = os.path.relpath(fp, start=folder_abs).replace("\\", "/")
                else:
                    doc_name = os.path.basename(fp)
                items.append((fp, doc_name))

        return items

    # ---------- 1) 预览 ----------

    def preview_folder(
        self,
        folder_path: str,
        *,
        recursive: bool = True,
        allowed_ext: Optional[List[str]] = None,
        ignore_hidden: bool = True,
        name_from: str = "basename",  # "basename" | "relative"
    ) -> List[Dict[str, str]]:
        """
        预览：只返回待上传文件清单，不执行上传。
        返回：[{ "file": <绝对路径>, "name": <将用于Dify的文档名> }, ...]
        """
        items = self._collect_candidates(
            folder_path=folder_path,
            recursive=recursive,
            allowed_ext=allowed_ext,
            ignore_hidden=ignore_hidden,
            name_from=name_from,
        )
        return [{"file": fp, "name": name} for fp, name in items]

    # ---------- 2) 上传 ----------

    def upload_folder(
        self,
        dataset_id: str,
        folder_path: Optional[str] = None,
        *,
        # 方案 A：直接传 folder_path，用与 preview 相同的筛选参数再次扫描
        recursive: bool = True,
        allowed_ext: Optional[List[str]] = None,
        ignore_hidden: bool = True,
        name_from: str = "basename",
        # 方案 B：若你已经 preview 过，可把结果直接传进来避免二次扫描
        items: Optional[List[Dict[str, str]]] = None,  # 形如 [{"file": "...", "name": "..."}]
        indexing_technique: str = "high_quality",
        process_rule: Optional[Dict[str, Any]] = None,
        on_error: str = "continue",  # "continue" | "raise"
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        上传：将预览的文件真正上传到 Dify 知识库。
        返回每个文件的处理结果：
        {
            "file": <本地绝对路径>,
            "status": "ok" | "error",
            "name": <文档名>,
            "reason": <失败原因或空>,
            "response": <成功时的API返回>
        }
        """
        if items is None:
            if not folder_path:
                raise ValueError("Either provide folder_path to scan or pass precomputed 'items'.")
            items = self.preview_folder(
                folder_path,
                recursive=recursive,
                allowed_ext=allowed_ext,
                ignore_hidden=ignore_hidden,
                name_from=name_from,
            )

        results: List[Dict[str, Any]] = []

        for it in items:
            fp = it["file"]
            doc_name = it["name"]
            try:
                resp = self.upload_document_file(
                    dataset_id=dataset_id,
                    file_path=fp,
                    name=doc_name,
                    indexing_technique=indexing_technique,
                    process_rule=process_rule,
                    **kwargs,
                )
                results.append(
                    {
                        "file": fp,
                        "status": "ok",
                        "name": doc_name,
                        "reason": "",
                        "response": resp,
                    }
                )
            except Exception as e:
                if on_error == "raise":
                    raise
                results.append(
                    {
                        "file": fp,
                        "status": "error",
                        "name": doc_name,
                        "reason": str(e),
                        "response": None,
                    }
                )

        return results
