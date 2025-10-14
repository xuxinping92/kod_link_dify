import json
import os
from typing import Any, Dict, Optional

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

        # 默认文档名
        if name is None:
            name = os.path.basename(file_path)

        # 构造 data 字段（JSON 字符串），包装必要字段
        payload = {
            "name": name,
            "indexing_technique": indexing_technique,
        }
        if process_rule is not None:
            payload["process_rule"] = process_rule

        # 若有其他自定义参数（如 mode 等），插入
        for k, v in kwargs.items():
            payload[k] = v

        # multipart/form-data 请求：一个 part 是 data（JSON 字符串），一个 part 是 file
        # 根据文档 “body: multipart/form-data” 要求 :contentReference[oaicite:2]{index=2}
        files = {
            # “data” 部分要传 JSON 文本
            "data": (None, json.dumps(payload), "application/json"),
            # “file” 部分要传实际文件内容
            "file": (name, open(file_path, "rb"), "application/octet-stream"),
        }

        resp = self.session.post(url, files=files, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()
