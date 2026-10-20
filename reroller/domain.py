# Python 3.14 | reroller/domain.py | Windows 11 / platform-independent parser
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from .i18n import Message, MESSAGES, msg


class RerollError(Exception):
    """An uncertainty that must prevent the next application."""

    def __init__(self, code: str | Message, **params):
        self.message = code if isinstance(code, Message) else msg(code, **params) if code in MESSAGES else msg("detail", detail=code)
        super().__init__(str(self.message))


NUMBER = r"[-+]?\d+(?:\.\d+)?"
NUMBERS = re.compile(NUMBER)
ROLL_RANGE = re.compile(r"\([-+]?\d+(?:\.\d+)?(?:\s*[-–—]\s*[-+]?\d+(?:\.\d+)?)?\)")
TAGS = re.compile(r"\s*\((fractured|implicit|enchant|rune|scourge|crafted|augmented|desecrated)\)", re.I)
FLAGS = {"Corrupted", "Mirrored", "Unidentified", "Fractured Item", "Synthesised Item", "Sanctified"}


def clean_line(line: str) -> str:
    line = TAGS.sub("", line)
    line = ROLL_RANGE.sub("", line)
    return " ".join(line.strip().split())


@dataclass(frozen=True)
class Modifier:
    text: str
    fractured: bool = False
    kind: str = "explicit"


@dataclass(frozen=True)
class Item:
    name: str
    base: str
    item_class: str
    rarity: str
    level: int
    modifiers: tuple[Modifier, ...]
    flags: frozenset[str]
    raw: str

    @property
    def fractures(self) -> tuple[str, ...]:
        return tuple(sorted(m.text for m in self.modifiers if m.fractured))

    @property
    def mutable(self) -> tuple[Modifier, ...]:
        return tuple(m for m in self.modifiers if not m.fractured and m.kind == "explicit")

    @property
    def identity(self) -> tuple:
        return self.name, self.base, self.item_class, self.rarity, self.level, self.flags, self.fractures

    @property
    def fingerprint(self) -> tuple:
        return self.identity, tuple(sorted((m.text, m.fractured, m.kind) for m in self.modifiers))


def parse_item(raw: str) -> Item:
    raw = raw.replace("\r\n", "\n").strip()
    blocks = re.split(r"\n-{4,}\n", raw)
    head = blocks[0].splitlines()
    rarity_line = next((i for i, line in enumerate(head) if line.startswith("Rarity: ")), None)
    if rarity_line is None:
        raise RerollError(msg('invalid_item_text'))
    rarity = head[rarity_line].split(": ", 1)[1]
    names = [s for s in head[rarity_line + 1:] if s.strip()]
    if not names:
        raise RerollError(msg('item_name_missing'))
    item_class = next((s.split(": ", 1)[1] for s in head if s.startswith("Item Class: ")), "")
    level_match = re.search(r"^Item Level: (\d+)\s*$", raw, re.M)
    if not level_match:
        raise RerollError(msg('item_level_missing'))
    flags = frozenset(line.strip() for line in raw.splitlines() if line.strip() in FLAGS)
    modifiers: list[Modifier] = []
    passed_level = False
    for block in blocks[1:]:
        lines = block.splitlines()
        if any(line.startswith("Item Level:") for line in lines):
            passed_level = True
            continue
        if not passed_level:
            continue
        current: list[str] = []
        fractured = False
        kind = "explicit"
        advanced = False

        def flush() -> None:
            nonlocal current
            if current:
                modifiers.append(Modifier("\n".join(current), fractured, kind))
                current = []

        for line in lines:
            line = line.strip()
            if not line or line in FLAGS or line.startswith(("Note:", "~", "Right click", "Place into", "Travel to")):
                continue
            if line.startswith("{") and line.endswith("}"):
                flush()
                advanced = True
                fractured = "fractured" in line.lower()
                kind = "implicit" if "implicit" in line.lower() else "explicit"
                if any(tag in line.lower() for tag in ("enchant", "rune modifier", "scourge")):
                    kind = "other"
                continue
            if line.startswith(("Sockets:", "Requirements:", "Requires ", "Item Class:", "Quality:", "Grants Skill:")):
                continue
            if not advanced:
                flush()
                fractured = "(fractured)" in line.lower()
                kind = "implicit" if "(implicit)" in line.lower() else "explicit"
                if any(t in line.lower() for t in ("(enchant)", "(rune)", "(scourge)")):
                    kind = "other"
            elif "(fractured)" in line.lower():
                fractured = True
            cleaned = clean_line(line)
            if cleaned:
                current.append(cleaned)
        flush()
    if "Fractured Item" in flags and not any(m.fractured for m in modifiers):
        raise RerollError(msg('fracture_unmarked'))
    return Item(names[0], names[-1], item_class, rarity, int(level_match[1]), tuple(modifiers), flags, raw)


def validate_item(item: Item) -> None:
    if item.rarity != "Rare":
        raise RerollError(msg('rare_required'))
    blocked = item.flags & {"Corrupted", "Mirrored", "Unidentified", "Sanctified"}
    if blocked:
        raise RerollError("blocked_item", flags=", ".join(sorted(blocked)))
    if not item.mutable:
        raise RerollError(msg('no_mutable'))


def parse_chaos_count(raw: str) -> int:
    blocks = re.split(r"\r?\n-{4,}\r?\n", raw.strip())
    lines = blocks[0].splitlines()
    try:
        i = lines.index("Rarity: Currency")
    except ValueError as exc:
        raise RerollError(msg('currency_wrong')) from exc
    if lines[i + 1:] != ["Chaos Orb"]:
        raise RerollError(msg('ordinary_chaos_only'))
    integer = r"(?:\d+|\d{1,3}(?:[, \u00a0\u202f]\d{3})+)"
    match = re.search(rf"^Stack Size: ({integer})/{integer}\s*$", raw, re.M)
    count = int(re.sub(r"[, \u00a0\u202f]", "", match[1])) if match else 0
    if count < 1:
        raise RerollError(msg('currency_empty'))
    return count


def template_from_text(text: str) -> str:
    # Keep '+' outside the placeholder; consume signs consistently when compiling.
    return NUMBERS.sub(lambda m: "+#" if m[0].startswith("+") else "#", clean_line(text))


@dataclass(frozen=True)
class Target:
    template: str
    minimums: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        if not self.template.strip() or self.template.count("#") != len(self.minimums):
            raise RerollError(msg('threshold_count'))
        if any(not n.is_finite() for n in self.minimums):
            raise RerollError(msg('threshold_finite'))

    @classmethod
    def create(cls, template: str, values: list[str]) -> Target:
        try:
            return cls(template.strip(), tuple(Decimal(v.strip().replace(",", ".")) for v in values))
        except InvalidOperation as exc:
            raise RerollError(msg('threshold_invalid')) from exc

    def matches(self, item: Item) -> bool:
        parts = self.template.casefold().split("#")
        pattern = re.escape(parts[0])
        for part in parts[1:]:
            # A literal plus belongs to the template; capture only the magnitude there.
            number = r"(\d+(?:\.\d+)?)" if pattern.endswith(r"\+") else rf"({NUMBER})"
            pattern += number + re.escape(part)
        pattern = pattern.replace(r"\ ", r"\s+").replace("\n", r"\s+")
        regex = re.compile(pattern, re.I)
        for modifier in item.modifiers:
            if modifier.kind != "explicit":
                continue
            match = regex.fullmatch(modifier.text.casefold())
            if match and all(Decimal(value) >= minimum for value, minimum in zip(match.groups(), self.minimums)):
                return True
        return False
