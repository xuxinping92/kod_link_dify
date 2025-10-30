import json
from typing import Any, Dict, Optional


class ProcessRule:
    """
    封装 Dify 文档处理规则（process_rule）。
    用于定义上传文档时的文本清洗、分段、embedding 生成等策略。
    """

    def __init__(
        self,
        *,
        mode: str = "custom",
        remove_extra_spaces: bool = True,
        remove_urls_emails: bool = True,
        remove_non_text: bool = False,
        separator: str = "###",
        max_tokens: int = 500,
        min_tokens: int = 100,
        overlap_tokens: int = 50,
        strategy: str = "recursive",
        embedding_enabled: bool = True,
        embedding_model: str = "text-embedding-3-small",
        embedding_provider: str = "openai",
        embedding_dimensions: Optional[int] = None,
        normalize_whitespace: bool = True,
        strip_html_tags: bool = False,
    ):
        self.mode = mode
        self.remove_extra_spaces = remove_extra_spaces
        self.remove_urls_emails = remove_urls_emails
        self.remove_non_text = remove_non_text
        self.separator = separator
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_tokens = overlap_tokens
        self.strategy = strategy
        self.embedding_enabled = embedding_enabled
        self.embedding_model = embedding_model
        self.embedding_provider = embedding_provider
        self.embedding_dimensions = embedding_dimensions
        self.normalize_whitespace = normalize_whitespace
        self.strip_html_tags = strip_html_tags

    def to_dict(self) -> Dict[str, Any]:
        """转为可直接传入 API 的 JSON dict。"""
        return {
            "mode": self.mode,
            "rules": {
                "pre_processing_rules": [
                    {"id": "remove_extra_spaces", "enabled": self.remove_extra_spaces},
                    {"id": "remove_urls_emails", "enabled": self.remove_urls_emails},
                    {"id": "remove_non_text", "enabled": self.remove_non_text},
                ],
                "segmentation": {
                    "separator": self.separator,
                    "max_tokens": self.max_tokens,
                    "min_tokens": self.min_tokens,
                    "overlap_tokens": self.overlap_tokens,
                    "strategy": self.strategy,
                },
                "embedding": {
                    "enabled": self.embedding_enabled,
                    "model": self.embedding_model,
                    "provider": self.embedding_provider,
                    "dimensions": self.embedding_dimensions,
                },
                "post_processing_rules": [
                    {"id": "normalize_whitespace", "enabled": self.normalize_whitespace},
                    {"id": "strip_html_tags", "enabled": self.strip_html_tags},
                ],
            },
        }

    def to_json(self) -> str:
        """返回 JSON 字符串（便于日志或直接请求使用）。"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
