from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..schemas import ExtractionRecord


class StructuredStore:
    """Append-only JSONL store for extracted records.

    This keeps things simple for phase-1 and is easy to ingest by the
    downstream ML engine. Each line is a single `ExtractionRecord.model_dump()`.
    """

    def __init__(self, path: str | Path = "literature_mining/storage/structured_store.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, record: ExtractionRecord) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            # 使用exclude_none=False确保所有字段都被包含（包括None值）
            f.write(json.dumps(record.model_dump(exclude_none=False), ensure_ascii=False) + "\n")

    def add_many(self, records: Iterable[ExtractionRecord]) -> int:
        n = 0
        with self.path.open("a", encoding="utf-8") as f:
            for r in records:
                # 使用exclude_none=False确保所有8个参数字段都被包含
                f.write(json.dumps(r.model_dump(exclude_none=False), ensure_ascii=False) + "\n")
                n += 1
        return n

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]