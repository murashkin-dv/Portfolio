import pathlib

import pytest

from project.server.main.config import get_settings

pytestmark = pytest.mark.asyncio


@pytest.mark.config
async def test_get_config_variable_positive() -> None:
    """
    Test for config variable
    """
    settings = get_settings()

    assert settings.base_dir == pathlib.Path(__file__).resolve().parents[1]
