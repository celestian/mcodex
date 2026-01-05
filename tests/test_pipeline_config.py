from __future__ import annotations

from pathlib import Path

import pytest

from mcodex.config import get_pipeline, validate_pipelines
from mcodex.errors import PipelineNotFoundError


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


def test_get_pipeline_missing_includes_available(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".mcodex").mkdir(parents=True)
    (repo / ".mcodex" / "config.yaml").write_text(
        "pipelines:\n  pdf:\n    steps:\n      - kind: pandoc\n        from: markdown\n"
        "        to: pdf\n  docx:\n    steps:\n      - kind: pandoc\n"
        "        from: markdown\n        to: docx\n",
        encoding="utf-8",
    )

    with pytest.raises(PipelineNotFoundError) as exc:
        get_pipeline("missing", repo_root=repo)

    msg = str(exc.value)
    assert "missing" in msg
    assert "pdf" in msg
    assert "docx" in msg
