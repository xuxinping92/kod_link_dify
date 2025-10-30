# kod_link_dify/sync.py
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

from kod_link_dify import DifyClient, KodClient


def sync_kod_file_to_dify(
    *,
    kod_client: KodClient,
    dify_client: DifyClient,
    dataset_id: str,
    kod_paths: Union[str, Iterable[str]],
    process_rule: Optional[str] = None,
    local_workdir: Optional[Union[str, Path]] = None,
    overwrite_local: bool = True,
    clean_local_after: bool = True,
    keep_local_copy_if_fail: bool = True,
) -> Dict[str, Any]:
    """
    将可道云的文档批量下载到本地临时目录后，上传到 Dify 知识库。

    参数
    ----
    kod_client :
        KodClient 实例，必须支持 download_file(path: str | list[str], save_to, overwrite)。
    dify_client :
        DifyClient 实例，必须支持 upload_folder(dataset_id, folder_path, process_rule_id)。
    dataset_id : str
        Dify 知识库 ID。
    kod_paths : str | list[str]
        可道云文件路径（单个或多个）。
    process_rule : str | None
        可选，Dify 的文档处理规则。
    local_workdir : str | Path | None
        可选，自定义本地工作目录。若不指定，则自动创建临时目录。
    overwrite_local : bool
        下载文件时是否覆盖本地同名文件。
    clean_local_after : bool
        上传成功后是否清理本地临时文件夹。
    keep_local_copy_if_fail : bool
        上传失败时是否保留本地文件夹。

    返回
    ----
    dict : {
        "workdir": str,             # 实际工作目录
        "downloaded": list[str],    # 下载到的文件路径
        "upload_result": dict|None, # Dify 上传结果
        "cleaned": bool,            # 是否已清理本地
    }
    """
    # 1) 创建本地工作目录
    created_tmp = False
    if local_workdir is None:
        workdir = Path(tempfile.mkdtemp(prefix="kod2dify_"))
        created_tmp = True
    else:
        workdir = Path(local_workdir)
        workdir.mkdir(parents=True, exist_ok=True)
    # 2) 从可道云批量下载文档
    downloaded_files = kod_client.download_file(
        path=kod_paths,
        save_to=workdir,
        overwrite=overwrite_local,
    )
    # 3) 上传整个文件夹到 Dify 知识库
    upload_result = None
    try:
        upload_result = dify_client.upload_folder(
            dataset_id=dataset_id,
            folder_path=workdir,
            process_rule=process_rule,
        )
    finally:
        # 4) 上传成功后可选择清理临时目录
        cleaned = False
        if clean_local_after and upload_result is not None:
            try:
                shutil.rmtree(workdir, ignore_errors=True)
                cleaned = True
            except Exception:
                cleaned = False
        elif clean_local_after and upload_result is None and not keep_local_copy_if_fail:
            try:
                shutil.rmtree(workdir, ignore_errors=True)
                cleaned = True
            except Exception:
                cleaned = False
        else:
            cleaned = False

    return {
        "workdir": str(workdir),
        "downloaded": (
            [str(p) for p in downloaded_files]
            if isinstance(downloaded_files, (list, tuple))
            else [str(downloaded_files)]
        ),
        "upload_result": upload_result,
        "cleaned": cleaned,
        "created_tmp": created_tmp,
    }


def sync_kod_folder_to_dify(
    *,
    kod_client: KodClient,
    dify_client: DifyClient,
    dify_dataset_id: str,
    kod_folder_path: str,
    process_rule: Optional[str] = None,
    local_workdir: Optional[Union[str, Path]] = None,
    overwrite_local: bool = True,
    clean_local_after: bool = True,
    keep_local_copy_if_fail: bool = True,
) -> Dict[str, Any]:
    """
    将可道云中【一个文件夹】的所有内容下载到本地，再整体上传到 Dify 知识库。

    参数
    ----
    kod_client :
        KodClient 实例，必须支持 download_folder_files(path, save_to, overwrite)。
    dify_client :
        DifyClient 实例，必须支持 upload_folder(dataset_id, folder_path, process_rule)。
    dify_dataset_id : str
        Dify 知识库 ID。
    kod_folder_path : str
        可道云上的文件夹路径，比如 "{source:486}/" 或 "个人空间/项目A/"。
    process_rule : str | None
        可选，Dify 的文档处理规则（传 id 或配置，看你 DifyClient 怎么封装的）。
    local_workdir : str | Path | None
        可选，本地工作目录；不传则自动建临时目录。
    overwrite_local : bool
        下载时是否覆盖本地已有同名文件。
    clean_local_after : bool
        上传成功后是否删除本地临时目录。
    keep_local_copy_if_fail : bool
        上传失败时是否保留本地文件。

    返回
    ----
    dict : {
        "workdir": str,             # 实际使用的本地目录
        "downloaded": list[str],    # 实际下载到的本地文件列表
        "upload_result": dict|None, # Dify 返回
        "cleaned": bool,            # 是否清理了本地目录
        "created_tmp": bool,        # 是否是这里新建的临时目录
    }
    """
    # 1) 准备本地工作目录
    created_tmp = False
    if local_workdir is None:
        workdir = Path(tempfile.mkdtemp(prefix="kod2dify_folder_"))
        created_tmp = True
    else:
        workdir = Path(local_workdir)
        workdir.mkdir(parents=True, exist_ok=True)

    # 2) 从可道云下载整个文件夹的内容到本地
    #    这里使用你刚刚写好的 download_folder_files
    downloaded_files = kod_client.download_folder_files(
        folder_path=kod_folder_path,
        save_to=workdir,
        overwrite=overwrite_local,
    )

    # 3) 上传整个目录到 Dify
    upload_result = None
    try:
        upload_result = dify_client.upload_folder(
            dataset_id=dify_dataset_id,
            folder_path=workdir,
            process_rule=process_rule,
        )
    finally:
        # 4) 处理本地清理逻辑
        cleaned = False
        if clean_local_after and upload_result is not None:
            # 上传成功再删
            try:
                shutil.rmtree(workdir, ignore_errors=True)
                cleaned = True
            except Exception:
                cleaned = False
        elif clean_local_after and upload_result is None and not keep_local_copy_if_fail:
            # 上传失败也要删（前提是用户不想保留失败的文件）
            try:
                shutil.rmtree(workdir, ignore_errors=True)
                cleaned = True
            except Exception:
                cleaned = False
        else:
            cleaned = False

    return {
        "workdir": str(workdir),
        "downloaded": [str(p) for p in downloaded_files] if downloaded_files else [],
        "upload_result": upload_result,
        "cleaned": cleaned,
        "created_tmp": created_tmp,
    }
