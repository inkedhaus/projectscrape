import json

rows = [{"a": 1}, {"a": 2}]


def test_ndjson_roundtrip(tmp_path):
    p = tmp_path / "demo.ndjson"
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    out = [json.loads(line) for line in p.read_text().splitlines()]
    assert out == rows
