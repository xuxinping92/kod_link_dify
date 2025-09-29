# tests/test_integration_options.py
import os
import pytest

from kod_link_dify import get_options

RUN_INTEGRATION = os.getenv("RUN_INTEGRATION_TESTS", "0") == "1"

@pytest.mark.skipif(not RUN_INTEGRATION, reason="Integration test disabled by default.")
def test_get_options_integration():
    opts = get_options()
    assert isinstance(opts, dict)