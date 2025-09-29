"""
Obtain and print configuration options of the Kod service.
"""

from kod_link_dify import KodClient

if __name__ == "__main__":
    kod_client = KodClient()
    kod_client.login()
    options = kod_client.get_options()
    print("Kod Options:", options)
