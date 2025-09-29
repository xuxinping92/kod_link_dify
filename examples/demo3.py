"""
Obtain and print a list of datasets from Dify.
"""

from kod_link_dify import DifyClient
from kod_link_dify.dify.config import api_key, base_url, request_timeout

if __name__ == "__main__":
    dify_client = DifyClient(
        base_url=base_url,
        api_key=api_key,
        timeout=request_timeout,
    )
    datasets = dify_client.list_datasets(page=1, limit=20)
    print("Datasets:", datasets)
