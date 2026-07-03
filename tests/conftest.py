import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def patch_save_path(tmp_path, monkeypatch):
    import save_data as sd_module

    monkeypatch.setattr(sd_module, "SAVE_PATH", str(tmp_path / "test_save.json"))
