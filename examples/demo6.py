"""
Upload document file to Dify with custom processing rules.
"""

from kod_link_dify import DifyClient
from kod_link_dify.dify.config import api_key, base_url, request_timeout

client = DifyClient(
    base_url=base_url,
    api_key=api_key,
    timeout=request_timeout,
)

process_rule = {
    "rules": {
        "pre_processing_rules": [
            {"id": "remove_extra_spaces", "enabled": True},
            {"id": "remove_urls_emails", "enabled": True},
        ],
        "segmentation": {
            "separator": "###",
            "max_tokens": 500,
        },
    },
    "mode": "custom",
}
result = client.upload_document_file(
    dataset_id='f6f44282-a4da-409c-8cfe-05edba8e351a',
    file_path=r"C:\Users\22959\Desktop\test_files\测试文档.docx",
    name="测试文档.docx",
    indexing_technique="high_quality",
    process_rule=process_rule,
)
print("Upload result:", result)
