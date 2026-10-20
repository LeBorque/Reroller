# Python 3.14 | reroller/demo.py | explicit simulation, never connects to the game
from __future__ import annotations

import threading

from .domain import parse_item
from .engine import Cancelled
from .i18n import msg


BLIGHT_WEAVER = """Item Class: Quarterstaves
Rarity: Rare
Blight Weaver
Sinister Quarterstaff
--------
Physical Damage: 55-91
Critical Hit Chance: 16.99% (augmented)
Attacks per Second: 1.40
--------
Requires: Level 67, 104 Dex, 41 Int
--------
Sockets: S S S
--------
Item Level: 86
--------
{ Fractured Suffix Modifier "of Unmaking" (Tier: 1) — Attack, Critical }
+4.99(4.41-5)% to Critical Hit Chance
{ Suffix Modifier "of the Falcon" (Tier: 5) — Attribute }
+20(17-20) to Dexterity
--------
Fractured Item
"""


def sample_with(line: str) -> str:
    return BLIGHT_WEAVER.replace('+20(17-20) to Dexterity', line)


class DemoConnection:
    def __init__(self, stop: threading.Event):
        self.stop, self.rolls = stop, 0

    def guard(self) -> None:
        if self.stop.is_set():
            raise Cancelled(msg("stopped"))

    def wait(self, seconds: float) -> None:
        if self.stop.wait(seconds):
            raise Cancelled(msg("stopped"))

    def read_item(self):
        self.guard()
        self.wait(0.035)
        lines = ['+20(17-20) to Dexterity', '+3 to Level of all Melee Skills', '+5 to Level of all Melee Skills']
        return parse_item(sample_with(lines[min(self.rolls, 2)]))

    def read_currency(self) -> int:
        self.guard()
        return 100 - self.rolls

    def apply_once(self, before_click) -> None:
        self.guard()
        before_click()
        self.rolls += 1

    def close(self) -> None:
        pass
