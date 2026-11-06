"""pytest 公共夹具。"""

from __future__ import annotations

from pathlib import Path

import pytest

from plate_gen import PlateGenerator


@pytest.fixture
def generator() -> PlateGenerator:
    return PlateGenerator()


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs"
