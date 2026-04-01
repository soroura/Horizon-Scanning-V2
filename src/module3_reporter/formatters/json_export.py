"""
JSON export formatter — array of merged ScanItem + ScoreCard dicts.
"""
from __future__ import annotations

import json
from datetime import date, datetime

from src.module1_scanner.models import ScanItem
from src.module2_scorer.models import ScoreCard


def _serialise(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Not serialisable: {type(obj)}")


def format_json(
    scorecards: list[ScoreCard],
    items_by_id: dict[str, ScanItem],
    run_meta: dict,
) -> str:
    records = []
    for sc in scorecards:
        item = items_by_id.get(sc.item_id)
        if item is None:
            continue
        record = {
            **item.model_dump(),
            **sc.model_dump(),
            "run_id": run_meta.get("run_id"),
        }
        records.append(record)

    output = {
        "run_meta": run_meta,
        "items": records,
    }
    return json.dumps(output, indent=2, default=_serialise)
