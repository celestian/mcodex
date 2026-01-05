from __future__ import annotations

import pytest

from mcodex.config import validate_pipelines


def test_validate_pipelines_rejects_empty() -> None:
    with pytest.raises(ValueError):
        validate_pipelines({})


def test_validate_pipelines_requires_steps_and_kinds() -> None:
    with pytest.raises(ValueError):
        validate_pipelines({"pdf": {}})

    with pytest.raises(ValueError):
        validate_pipelines({"pdf": {"steps": []}})

    with pytest.raises(ValueError):
        validate_pipelines({"pdf": {"steps": [{"to": "pdf"}]}})

    validate_pipelines(
        {"docx": {"steps": [{"kind": "pandoc", "from": "markdown", "to": "docx"}]}}
    )
