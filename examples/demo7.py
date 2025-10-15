"""
Upload a folder of documents to Dify with custom processing rules.
"""

from kod_link_dify import DifyClient
from kod_link_dify.dify.config import api_key, base_url, request_timeout

dataset_id = "f6f44282-a4da-409c-8cfe-05edba8e351a"
folder = r"C:\Users\22959\Desktop\test_files"
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


client = DifyClient(
    base_url=base_url,
    api_key=api_key,
    timeout=request_timeout,
)


# --- 第一步：预览 ---
preview = client.preview_folder(
    folder,
    recursive=True,
    allowed_ext=[".pdf", ".docx", ".txt"],
    name_from="relative",
)
print("将要上传的文件数：", len(preview))
for p in preview[:5]:
    print(p["name"], "←", p["file"])

# --- 第二步：上传（推荐传 preview，避免二次扫描）---
results = client.upload_folder(
    dataset_id=dataset_id,
    items=preview,  # ✅ 用预览的结果
    process_rule=process_rule,  # ✅ 传入 process_rule
    indexing_technique="high_quality",  # ✅ 高质量向量索引
)

# --- 结果统计 ---
ok = sum(1 for r in results if r["status"] == "ok")
err = sum(1 for r in results if r["status"] == "error")
print(f"完成：成功 {ok} 个，失败 {err} 个 / 总计 {len(results)}")
