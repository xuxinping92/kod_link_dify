"""
Obtain and print a list of datasets from Dify.
"""

from kod_link_dify.dify import list_datasets

if __name__ == "__main__":
    datasets = list_datasets(page=1, limit=20)
    print("Datasets:", datasets)
