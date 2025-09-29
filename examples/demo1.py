"""
Obtain and print an authentication token from Kod using configuration settings.
"""

from kod_link_dify import KodClient
from kod_link_dify.kod.config import (
    base_url,
    password,
    request_timeout,
    username,
)

if __name__ == "__main__":
    print("Base URL:", base_url)
    print("Username:", username)
    print("Password:", password)
    print("Request Timeout:", request_timeout)
    kod_client = KodClient(
        base_url=base_url,
        username=username,
        password=password,
    )
    token = kod_client.login()
    print("Token:", token)
