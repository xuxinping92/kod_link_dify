from kod_link_dify import DifyClient, KodClient, sync_kod_folder_to_dify
from kod_link_dify.dify import ProcessRule
from kod_link_dify.dify.config import api_key
from kod_link_dify.dify.config import base_url as dify_url
from kod_link_dify.kod.config import base_url as kod_url
from kod_link_dify.kod.config import password, username

kod = KodClient(
    base_url=kod_url,
    username=username,
    password=password,
)
kod.login()
dify = DifyClient(
    base_url=dify_url,
    api_key=api_key,
)

kod_folder_path = "{source:486}/"
dataset_id = "f6f44282-a4da-409c-8cfe-05edba8e351a"
folder = r"C:\Users\22959\Desktop\test_files"

process_rule = ProcessRule()

result = sync_kod_folder_to_dify(
    kod_client=kod,
    dify_client=dify,
    dify_dataset_id=dataset_id,
    kod_folder_path=kod_folder_path,
    process_rule=process_rule.to_dict(),
    local_workdir=folder,
    overwrite_local=True,
    clean_local_after=True,
    keep_local_copy_if_fail=True,
)

print("✅ 上传成功:", bool(result["upload_result"]))
print("📂 下载到目录:", result["workdir"])
print("📄 文件:", result["downloaded"])
