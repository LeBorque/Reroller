# Python 3.14 | reroller/settings.py | local application settings
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path

from .windows import Calibration
from .domain import RerollError
from .i18n import LANGUAGES


def data_directory() -> Path:
    path = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "PoE2Reroller"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_settings() -> dict:
    path = data_directory() / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return migrate_settings(data) if isinstance(data, dict) else migrate_settings({})
    except (OSError, ValueError):
        return migrate_settings({})


def migrate_settings(data: dict) -> dict:
    result = dict(data)
    result["version"] = 2
    if result.get("language") not in LANGUAGES:
        result["language"] = "sv-SE"
    for key in ("category_id", "modifier_id"):
        if not isinstance(result.get(key), str):
            result[key] = None
    if not isinstance(result.get("template"), str):
        result["template"] = "+# to Level of all Melee Skills"
    if not isinstance(result.get("minimums"), list) or not all(isinstance(v, str) for v in result["minimums"]):
        result["minimums"] = ["5"]
    return result


def load_calibration(data: dict) -> Calibration | None:
    try:
        source = data["calibration"]
        result = Calibration(tuple(source["bounds"]),
                             tuple(source["currency"]) if source.get("currency") is not None else None,
                             tuple(source["item"]) if source.get("item") is not None else None)
        result.validate()
        return result
    except (KeyError, TypeError, ValueError, AttributeError, RerollError):
        # Malformed local settings must not enable a partially guessed calibration.
        return None


def save_settings(calibration: Calibration | None, template: str, minimums: list[str], *,
                  language: str = "sv-SE", category_id: str | None = None, modifier_id: str | None = None) -> None:
    data = {"version": 2, "calibration": asdict(calibration) if calibration else None,
            "template": template, "minimums": minimums, "language": language,
            "category_id": category_id, "modifier_id": modifier_id}
    path = data_directory() / "settings.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
