from __future__ import annotations

from pathlib import Path

import yaml

from mcodex.metadata import load_metadata


def test_load_metadata_upgrades_v0_to_v1(tmp_path: Path) -> None:
    p = tmp_path / "metadata.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "id": "x",
                "title": "T",
                "slug": "t",
                "created_at": "2026-01-03T00:00:00+01:00",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    data = load_metadata(p)

    assert data["metadata_version"] == 1
    assert data["authors"] == []

    again = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert again["metadata_version"] == 1
