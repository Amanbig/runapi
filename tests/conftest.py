import os

import pytest


@pytest.fixture(autouse=True)
def _isolate_environment():
    """Restore os.environ and the global config after every test.

    ``.env`` loading and CLI commands (``runapi start``) mutate the process environment.
    """
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)
    try:
        from runapi.config import load_config

        load_config()
    except Exception:  # config invalid because a test left bad state; next test resets
        pass
