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
