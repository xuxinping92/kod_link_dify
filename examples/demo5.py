"""
Obtain document from Kod and save it to local desktop.
"""

from pathlib import Path

from kod_link_dify.kod.api import KodClient

# 示例：下载文件到桌面
client = KodClient()
client.login()

# 获取 Windows 桌面路径
desktop = Path.home() / "Desktop"

# 1) 通过 {source:ID} 下载（接口示例）
local_path = client.download_file(
    path=["{source:3543}/", "{source:3544}/"],
    save_to=desktop,
    overwrite=True,
)
print("saved to:", local_path)

# 2) 通过可读路径下载（如果你的 path 是这种）
# local_path = client.download_file(path="个人空间/我的文档/测试文档2.docx", save_to=desktop, overwrite=True)
# print("saved to:", local_path)
