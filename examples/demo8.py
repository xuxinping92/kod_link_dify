from kod_link_dify import DifyClient, KodClient, sync_kod_file_to_dify

kod = KodClient()
kod.login()
dify = DifyClient()

kod_paths = ["{source:3543}/", "{source:3544}/"]
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
