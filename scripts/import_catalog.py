# Python 3.14 | scripts/import_catalog.py | normalize retained REA ModsView captures
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def plain(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", str(value))).strip()


class ModifierHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.values = [], []
        self.span_depth = 0
        self.value_depth = None
        self.value_parts = []
        self.supported = True

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            self.span_depth += 1
            if self.value_depth is None and "mod-value" in dict(attrs).get("class", "").split():
                self.value_depth = self.span_depth
                self.value_parts = []
        if tag == "br":
            (self.value_parts if self.value_depth is not None else self.parts).append("\n")

    def handle_endtag(self, tag):
        if tag != "span":
            return
        if self.value_depth == self.span_depth:
            raw = "".join(self.value_parts).strip().replace("−", "-")
            prefix = "+" if raw.startswith("+") else ""
            sign = -1 if raw.startswith("-(") else 1
            cleaned = raw.lstrip("+").removeprefix("-(").strip("() ")
            match = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)(?:\s*[-–—]\s*([-+]?\d+(?:\.\d+)?))?", cleaned)
            if match:
                low, high = Decimal(match[1]) * sign, Decimal(match[2] or match[1]) * sign
                self.values.append([str(min(low, high)), str(max(low, high))])
                self.parts.append(prefix + "#")
            else:
                self.supported = False
                self.parts.append(raw)
            self.value_depth = None
        self.span_depth -= 1

    def handle_data(self, data):
        (self.value_parts if self.value_depth is not None else self.parts).append(data)

    @classmethod
    def parse(cls, source: str):
        parser = cls()
        parser.feed(source)
        template = "\n".join(" ".join(line.split()) for line in "".join(parser.parts).splitlines()).strip()
        supported = parser.supported and template.count("#") == len(parser.values) and len(parser.values) <= 12
        return template, parser.values, supported


def normalize_category(raw: dict, label: str) -> tuple[dict, dict]:
    data = raw["data"]
    category_id = raw["url"].rstrip("/").rsplit("/", 1)[-1]
    records = {}
    group_counts = {}
    for source, rows in data.items():
        if not isinstance(rows, list):
            continue
        if source in {"ids", "attr", "tags"}:
            continue  # ModsView metadata, not modifier records.
        group_counts[source] = len(rows)
        for ordinal, row in enumerate(rows):
            if not isinstance(row, dict) or "str" not in row:
                raise ValueError(f"Unrecognized modifier record: {category_id}/{source}/{ordinal}")
            template, values, supported = ModifierHTML.parse(row["str"])
            generation = int(row.get("ModGenerationTypeID", 0))
            families = sorted(row.get("ModFamilyList", []))
            identity = json.dumps([category_id, source, generation, families, template], ensure_ascii=False)
            key = hashlib.sha256(identity.encode()).hexdigest()[:24]
            modifier = records.setdefault(key, {"id": key, "template": template, "source": source,
                                               "generation": generation, "families": families,
                                               "supported": supported, "example": plain(row["str"].replace("<br>", "\n")), "tiers": []})
            modifier["supported"] = modifier["supported"] and supported
            modifier["tiers"].append({"name": plain(row.get("Name", "")), "level": int(row.get("Level", 0)),
                                      "weight": float(row.get("DropChance", 0)), "values": values,
                                      "code": row.get("Code"), "hover": row.get("hover"),
                                      "spawn_tags": row.get("spawn_no", []), "record_ordinal": ordinal})
    for modifier in records.values():
        modifier["tiers"].sort(key=lambda t: (t["level"], t["name"]))
    game_class = {"Jewel": "Jewels", "Relic": "Relics", "TowerAugmentation": "Tablets"}.get(data["baseitem"].get("cn"), plain(data["baseitem"]["link_name"]))
    if category_id.startswith("Waystones_"):
        game_class = "Waystones"
    bases = raw.get("bases", [])
    if data["baseitem"].get("cn") in {"Jewel", "Relic", "TowerAugmentation"}:
        bases = sorted(set(bases + [label]))
    category = {"id": category_id, "label": label,
                "game_class": game_class, "bases": bases,
                "url": raw["url"], "source_labels": {k: plain(v.get("title", k)) for k, v in data.get("config", {}).items()},
                "modifiers": sorted(records.values(), key=lambda m: (m["template"].casefold(), m["source"], m["id"]))}
    manifest = {"url": raw["url"], "date": raw["date"], "evidence_id": raw["evidence_id"],
                "groups": group_counts, "records": sum(group_counts.values()), "choices": len(records),
                "unsupported_records": sum(len(m["tiers"]) for m in records.values() if not m["supported"])}
    return category, manifest


def build(input_dir: Path = ROOT / "artifacts/poe2db", output: Path = ROOT / "reroller/data/catalog.json.gz") -> dict:
    index = json.loads((input_dir / "index.json").read_text(encoding="utf-8"))
    categories, sources, missing = [], {}, []
    for entry in index["categories"]:
        identifier = entry["url"].rstrip("/").rsplit("/", 1)[-1]
        path = input_dir / "raw" / f"{identifier}.json"
        if not path.exists():
            missing.append(identifier)
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw["url"] != entry["url"]:
            raise ValueError(f"Source identity mismatch: {identifier}")
        category, manifest = normalize_category(raw, entry["label"])
        manifest["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        categories.append(category)
        sources[identifier] = manifest
    expected = [e["url"].rstrip("/").rsplit("/", 1)[-1] for e in index["categories"]]
    manifest = {"schema": 1, "source": index["url"], "date": index["date"], "index_evidence_id": index["evidence_id"],
                "complete": not missing and len(categories) == len(expected), "expected_categories": expected,
                "missing_categories": missing, "sources": sources,
                "records": sum(s["records"] for s in sources.values()),
                "choices": sum(s["choices"] for s in sources.values())}
    def remove_external_labels(value):
        if isinstance(value, dict):
            return {key: remove_external_labels(item) for key, item in value.items()}
        if isinstance(value, list):
            return [remove_external_labels(item) for item in value]
        if isinstance(value, str) and "poe2db" in value.casefold():
            return ""
        return value

    document = remove_external_labels({"manifest": manifest, "categories": categories})
    manifest = document["manifest"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as packed:
            packed.write(json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    (output.parent / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in {"sources", "expected_categories"}}, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    build()
