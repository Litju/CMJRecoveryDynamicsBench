"""The private-source harness must reject unpinned bytes before execution."""

from pathlib import Path

import pytest
from verify_feature_projection import SOURCE_AUTHORITY, verify


def test_wrong_source_pin_rejects_before_source_execution(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    source.write_text('raise RuntimeError("unverified source executed")')
    with pytest.raises(ValueError, match="source identity mismatch"):
        verify(source, expected_source_sha256="0" * 64)
    assert SOURCE_AUTHORITY == "RES-546-EXTRACTOR-AUTHORITY-01"
