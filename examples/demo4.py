"""
Obtain document permission list from Kod and print it.
"""

from kod_link_dify.kod.api import KodClient

client = KodClient()
client.login()
perm_data = client.get_doc_permission_list()
print("文档权限列表:", perm_data)  # 拿到角色与权限配置，可直接用于表格展示或本地缓存
