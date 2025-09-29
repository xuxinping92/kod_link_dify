from kod_link_dify.kod.api import KodClient

if __name__ == "__main__":
    kod = KodClient()
    kod.login()

    # 1. 列出根目录
    items = kod.list_dir("io_/")
    for item in items:
        print(f"{item['type']}: {item['name']}  ->  {item['path']}")

    # 2. 获取某个文件的信息
    file_path = "io_/home/xxu/test/test1.txt"
    info = kod.get_file_info(file_path)
    print("文件信息：", info)
