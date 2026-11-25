"""Integration tests should run with docker-compose services."""

import pytest


@pytest.mark.integration
def test_services_placeholder():
    assert True
