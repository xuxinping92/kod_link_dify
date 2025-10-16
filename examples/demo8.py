from kod_link_dify import DifyClient, KodClient, sync_kod_file_to_dify

kod = KodClient()
kod.login()
dify = DifyClient()

kod_paths = ["{source:3543}/", "{source:3544}/"]
dataset_id = "f6f44282-a4da-409c-8cfe-05edba8e351a"
folder = r"C:\Users\22959\Desktop\test_files"
process_rule = {
    "mode": "custom",  # 表示自定义模式（而非使用 dataset 的默认规则）
    "rules": {
        "pre_processing_rules": [
            {"id": "remove_extra_spaces", "enabled": True},  # 去除多余空格
            {"id": "remove_urls_emails", "enabled": True},  # 去除URL与邮箱
            {"id": "remove_non_text", "enabled": False},  # 可选：是否去掉非文字内容（表格/图像）
        ],
        "segmentation": {
            "separator": "###",  # 自定义文本段落分隔符
            "max_tokens": 500,  # 每段最大 token 数（可视为 chunk 长度）
            "min_tokens": 100,  # 最小 chunk 大小（避免太短）
            "overlap_tokens": 50,  # 相邻段之间的重叠
            "strategy": "recursive",  # 拆分策略，可为 "recursive" 或 "separator"
        },
        "embedding": {
            "enabled": True,  # 是否启用向量生成
            "provider": "openai",  # 向量模型来源，可改为 "local"、"baichuan" 等
            "model": "text-embedding-3-small",  # 向量模型名称
            "dimensions": None,  # 可选，指定向量维度（若模型支持）
        },
        "post_processing_rules": [
            {"id": "normalize_whitespace", "enabled": True},  # 规范化空白
            {"id": "strip_html_tags", "enabled": False},  # 移除 HTML 标签（若有）
        ],
    },
}


result = sync_kod_file_to_dify(
    kod_client=kod,
    dify_client=dify,
    dataset_id=dataset_id,
    kod_paths=kod_paths,
    process_rule=process_rule,
    local_workdir=folder,
    overwrite_local=True,
    clean_local_after=True,
    keep_local_copy_if_fail=True,
)

print("✅ 上传成功:", bool(result["upload_result"]))
print("📂 下载到目录:", result["workdir"])
print("📄 文件:", result["downloaded"])
