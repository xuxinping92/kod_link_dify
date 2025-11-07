"""
Obtain files from a specified folder in Kodbox and save them to the desktop.
"""

from kod_link_dify.kod.api import KodClient

# 示例：下载文件夹内的所有文件到桌面
client = KodClient()
client.login()

# 1) 通过 {source:ID} 下载（接口示例）
saved = client.download_folder_files_recursive(
    folder_path="{source:486}/",
    save_to=r"C:\Users\22959\Desktop\test_files",
    chunk_size=1024 * 1024,
    overwrite=True,
    timeout=30,
    keep_structure=False,
)
print(saved)
