"""
Obtain and print an authentication token from Kod using configuration settings.
"""

from kod_link_dify.kod import get_token
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
    token = get_token(
        user=username,
        pwd=password,
        base=base_url,
        timeout=request_timeout,
    )
    print("Token:", token)
