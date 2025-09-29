import requests
from typing import Dict, Any, Optional
from .config import base_url, api_key, request_timeout

class DifyKB:
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
        self.s = session or requests.Session()
        if not api_key:
            # 允许无密钥初始化，但调用时会 401；这里仅做提醒，不抛错
            pass
        self.s.headers.update({"Authorization": f"Bearer {api_key}"})
        self.timeout = timeout

    # ========== Datasets ==========

    def list_datasets(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """知识库列表（分页）
        GET /v1/datasets?page=1&limit=20
        文档出处：“知识库列表”段落
        """
        url = f"{self.base}/v1/datasets"
        r = self.s.get(url, params={"page": page, "limit": limit}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ========== Documents ==========

    def list_documents(self, dataset_id: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """某知识库内的文档列表
        GET /v1/datasets/{dataset_id}/documents
        文档出处：“知识库文档列表”段落
        """
        url = f"{self.base}/v1/datasets/{dataset_id}/documents"
        r = self.s.get(url, params={"page": page, "limit": limit}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ========== Helpers ==========

    @classmethod
    def from_config(cls) -> "DifyKB":
        """使用 dify.config 中的默认配置创建客户端"""
        return cls(base_url=base_url, api_key=api_key, timeout=request_timeout)

# ===== 顶层便捷函数（对齐 KOD 部分的使用体验） =====

def get_client() -> DifyKB:
    """返回基于配置初始化的 DifyKB 客户端"""
    return DifyKB.from_config()

def list_datasets(page: int = 1, limit: int = 20) -> Dict[str, Any]:
    """便捷方法：列出知识库（使用配置中的 base_url/api_key）"""
    return get_client().list_datasets(page=page, limit=limit)

def list_documents(dataset_id: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
    """便捷方法：列出指定知识库的文档列表（使用配置中的 base_url/api_key）"""
    return get_client().list_documents(dataset_id=dataset_id, page=page, limit=limit)