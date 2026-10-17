from export_openapi import SNAPSHOT, render


def test_openapi_snapshot_is_current() -> None:
    assert SNAPSHOT.read_text(encoding="utf-8") == render(), (
        "backend/openapi.json is out of date. Regenerate it with "
        "`uv run python export_openapi.py` (in backend/), then regenerate the frontend types "
        "with `npm run gen:api` (in frontend/)."
    )
