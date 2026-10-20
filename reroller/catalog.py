# Python 3.14 | reroller/catalog.py | offline modifier catalog and eligibility
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import gzip
import json
from pathlib import Path
import re

from .domain import Item, Target, RerollError


@dataclass(frozen=True)
class CatalogModifier:
    id: str
    category_id: str
    template: str
    source: str
    generation: int
    families: tuple[str, ...]
    tiers: tuple[dict, ...]
    supported: bool
    example: str

    @property
    def chaos(self) -> bool:
        return self.source == "normal" and self.generation in (1, 2) and self.supported and any(t["weight"] > 0 for t in self.tiers)

    def available_tiers(self, level: int) -> tuple[dict, ...]:
        return tuple(t for t in self.tiers if t["weight"] > 0 and t["level"] <= level)


@dataclass(frozen=True)
class Category:
    id: str
    label: str
    game_class: str
    bases: tuple[str, ...]
    url: str
    source_labels: dict[str, str]
    modifiers: tuple[CatalogModifier, ...]

    @property
    def group_key(self) -> str:
        if self.id.startswith(("Gloves_", "Boots_", "Body_Armours_", "Helmets_")):
            return "group_armour"
        if self.id in {"Amulets", "Rings", "Belts"}:
            return "group_accessories"
        if self.id in {"Quivers", "Bucklers", "Foci"} or self.id.startswith("Shields_"):
            return "group_offhands"
        if self.game_class == "Jewels":
            return "group_jewels"
        if self.id.endswith("_Flasks") or self.id == "Charms":
            return "group_flasks"
        if self.game_class == "Relics":
            return "group_relics"
        if self.game_class == "Tablets":
            return "group_tablets"
        if self.id.startswith("Waystones_"):
            return "group_waystones"
        return "group_weapons"

    @property
    def base_affixes(self) -> tuple[CatalogModifier, ...]:
        return tuple(m for m in self.modifiers if m.chaos)


class Catalog:
    def __init__(self, document: dict):
        self.manifest = document["manifest"]
        self.categories: dict[str, Category] = {}
        self.modifiers: dict[str, CatalogModifier] = {}
        for raw in document["categories"]:
            records = tuple(CatalogModifier(category_id=raw["id"], families=tuple(m["families"]),
                                           tiers=tuple(m["tiers"]), **{k: v for k, v in m.items() if k not in {"families", "tiers"}})
                            for m in raw["modifiers"])
            category = Category(modifiers=records, bases=tuple(raw["bases"]),
                                **{k: v for k, v in raw.items() if k not in {"bases", "modifiers"}})
            self.categories[category.id] = category
            for modifier in records:
                if modifier.id in self.modifiers:
                    raise ValueError("Duplicate catalog modifier ID")
                self.modifiers[modifier.id] = modifier
        self.complete = self.manifest.get("complete") is True and set(self.manifest["expected_categories"]) == set(self.categories)

    @classmethod
    def load(cls, path: Path | None = None) -> Catalog:
        path = path or Path(__file__).parent / "data" / "catalog.json.gz"
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            return cls(json.load(stream))

    def candidates(self, item: Item) -> tuple[Category, ...]:
        matching = tuple(c for c in self.categories.values() if c.game_class.casefold() == item.item_class.casefold())
        by_base = tuple(c for c in matching if item.base in c.bases)
        return by_base or matching

    def infer(self, item: Item) -> str | None:
        candidates = self.candidates(item)
        return candidates[0].id if len(candidates) == 1 else None

    def source_label(self, modifier: CatalogModifier) -> str:
        return self.categories[modifier.category_id].source_labels.get(modifier.source, modifier.source.replace("_", " ").title())

    def chaos_alternatives(self, modifier: CatalogModifier) -> tuple[CatalogModifier, ...]:
        return tuple(m for m in self.categories[modifier.category_id].modifiers if m.chaos and m.template == modifier.template)

    def validate(self, category_id: str, modifier_id: str | None, item: Item, target: Target) -> None:
        # A target already on the item is always a zero-currency success, even for a special source.
        if target.matches(item):
            return
        if not self.complete:
            raise RerollError("catalog_incomplete")
        category = self.categories.get(category_id)
        if category is None or category not in self.candidates(item):
            raise RerollError("category_mismatch")
        if modifier_id is None:
            return  # Explicit custom-template mode preserves existing behavior.
        modifier = self.modifiers.get(modifier_id)
        if modifier is None or modifier.category_id != category_id or modifier.template != target.template:
            raise RerollError("catalog_selection_invalid")
        alternatives = self.chaos_alternatives(modifier)
        if not alternatives:
            raise RerollError("modifier_not_chaos")
        tiers = tuple(t for alternative in alternatives for t in alternative.available_tiers(item.level))
        if not tiers:
            raise RerollError("modifier_level", level=item.level)
        possible = [t for t in tiers if len(t["values"]) == len(target.minimums)
                    and all(Decimal(bounds[1]) >= minimum for bounds, minimum in zip(t["values"], target.minimums))]
        if not possible:
            raise RerollError("modifier_values", level=item.level)
        viable = {m.id for m in alternatives if any(t in possible for t in m.available_tiers(item.level))}
        # Resolve locked affix families only when matching the catalog text is unambiguous.
        for locked in (m for m in item.modifiers if m.fractured):
            families = set()
            for entry in category.modifiers:
                if entry.source == "normal" and self._text_matches(entry.template, locked.text):
                    families.add(entry.families)
            if len(families) == 1:
                locked_families = set(next(iter(families)))
                viable = {identifier for identifier in viable if not locked_families & set(self.modifiers[identifier].families)}
        if not viable:
            raise RerollError("modifier_fracture_conflict")

    @staticmethod
    def _text_matches(template: str, text: str) -> bool:
        pattern = re.escape(template).replace(r"\#", r"[-+]?\d+(?:\.\d+)?")
        pattern = pattern.replace(r"\ ", r"\s+").replace("\n", r"\s+")
        return re.fullmatch(pattern, text, re.I) is not None


def search_entries(entries: list[tuple[str, str]], query: str) -> list[tuple[str, str]]:
    words = query.casefold().split()
    return [entry for entry in entries if all(word in entry[1].casefold() for word in words)]
