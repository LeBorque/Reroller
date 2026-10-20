import unittest

from reroller.domain import (parse_item, validate_item, parse_chaos_count, Target,
                            RerollError, template_from_text)
from reroller.demo import BLIGHT_WEAVER, sample_with


class ParserTests(unittest.TestCase):
    def test_real_zyon_item_advanced_fracture(self):
        item = parse_item(BLIGHT_WEAVER)
        validate_item(item)
        self.assertEqual(item.name, "Blight Weaver")
        self.assertEqual(item.base, "Sinister Quarterstaff")
        self.assertEqual(item.level, 86)
        self.assertEqual(item.fractures, ("+4.99% to Critical Hit Chance",))
        self.assertEqual([m.text for m in item.mutable], ["+20 to Dexterity"])

    def test_one_mutable_modifier_is_still_rare(self):
        raw = BLIGHT_WEAVER.replace('{ Fractured Suffix Modifier "of Unmaking" (Tier: 1) — Attack, Critical }\n+4.99(4.41-5)% to Critical Hit Chance\n', '').replace('\nFractured Item', '')
        item = parse_item(raw)
        validate_item(item)
        self.assertEqual(len(item.mutable), 1)
        self.assertFalse(item.fractures)

    def test_plain_fractured_annotation(self):
        raw = BLIGHT_WEAVER.replace('{ Fractured Suffix Modifier "of Unmaking" (Tier: 1) — Attack, Critical }\n', '').replace('+4.99(4.41-5)% to Critical Hit Chance', '+4.99% to Critical Hit Chance (fractured)').replace('{ Suffix Modifier "of the Falcon" (Tier: 5) — Attribute }\n', '')
        self.assertEqual(parse_item(raw).fractures, ("+4.99% to Critical Hit Chance",))

    def test_unmarked_fracture_rejected(self):
        raw = BLIGHT_WEAVER.replace("Fractured Suffix Modifier", "Suffix Modifier")
        with self.assertRaises(RerollError):
            parse_item(raw)

    def test_multiline_modifier_is_one_affix(self):
        raw = sample_with("Adds 10(8-12) to 20(18-22) Physical Damage\n10(8-12)% increased Stun Buildup")
        item = parse_item(raw)
        self.assertEqual(len(item.mutable), 1)
        self.assertIn("\n", item.mutable[0].text)
        self.assertTrue(Target.create("Adds # to # Physical Damage 10% increased Stun Buildup", ["10", "20"]).matches(item))

    def test_implicit_not_mutable_and_not_target_match(self):
        raw = sample_with("+5 to Level of all Melee Skills").replace('{ Suffix Modifier "of the Falcon" (Tier: 5) — Attribute }', '{ Implicit Modifier — Attack }')
        item = parse_item(raw)
        self.assertFalse(item.mutable)
        self.assertFalse(Target.create("+# to Level of all Melee Skills", ["5"]).matches(item))

    def test_invalid_items(self):
        for flag in ("Unidentified", "Corrupted", "Mirrored", "Sanctified"):
            with self.subTest(flag=flag), self.assertRaises(RerollError):
                validate_item(parse_item(BLIGHT_WEAVER + "\n" + flag))
        with self.assertRaises(RerollError):
            validate_item(parse_item(BLIGHT_WEAVER.replace("Rarity: Rare", "Rarity: Magic")))

    def test_no_item_and_no_level_rejected(self):
        for raw in ("", "some unrelated clipboard text", BLIGHT_WEAVER.replace("Item Level: 86", "")):
            with self.subTest(raw=raw[:20]), self.assertRaises(RerollError):
                parse_item(raw)

    def test_regular_chaos_only_and_count(self):
        raw = "Item Class: Stackable Currency\nRarity: Currency\nChaos Orb\n--------\nStack Size: 1,153/5,000\n--------\nRemoves a random modifier"
        self.assertEqual(parse_chaos_count(raw), 1153)
        for other in ("Greater Chaos Orb", "Perfect Chaos Orb", "Exalted Orb"):
            with self.subTest(other=other), self.assertRaises(RerollError):
                parse_chaos_count(raw.replace("Chaos Orb", other))
        for other in ("", raw.replace("1,153", "0"), raw.replace("Stack Size", "Count")):
            with self.assertRaises(RerollError):
                parse_chaos_count(other)

    def test_live_chaos_unicode_thousands_separator(self):
        for separator in ('\u00a0', '\u202f', ' '):
            raw = f'Item Class: Stackable Currency\r\nRarity: Currency\r\nChaos Orb\r\n--------\r\nStack Size: 1{separator}153/20\r\n'
            with self.subTest(separator=repr(separator)):
                self.assertEqual(parse_chaos_count(raw), 1153)


class TargetTests(unittest.TestCase):
    def test_melee_threshold(self):
        target = Target.create("+# to Level of all Melee Skills", ["5"])
        for value, expected in ((4, False), (5, True), (6, True)):
            self.assertEqual(target.matches(parse_item(sample_with(f"+{value} to Level of all Melee Skills"))), expected)

    def test_no_substring_match(self):
        item = parse_item(sample_with("+5 to Level of all Elemental Skills"))
        self.assertFalse(Target.create("+# to Level of all Melee Skills", ["5"]).matches(item))

    def test_fracture_can_satisfy_goal(self):
        self.assertTrue(Target.create("+#% to Critical Hit Chance", ["4.99"]).matches(parse_item(BLIGHT_WEAVER)))

    def test_multi_values_and_decimals(self):
        item = parse_item(sample_with("Adds 10 to 20 Physical Damage"))
        self.assertTrue(Target.create("Adds # to # Physical Damage", ["9,5", "20"]).matches(item))
        self.assertFalse(Target.create("Adds # to # Physical Damage", ["11", "20"]).matches(item))

    def test_case_whitespace_and_text_goal(self):
        item = parse_item(sample_with("Cannot be Frozen"))
        self.assertTrue(Target.create("cannot be frozen", []).matches(item))
        self.assertTrue(Target.create("+# to dexterity", ["20"]).matches(parse_item(BLIGHT_WEAVER)))

    def test_invalid_thresholds(self):
        for values in ([""], ["NaN"], ["Infinity"], ["word"], [], ["1", "2"]):
            with self.subTest(values=values), self.assertRaises(RerollError):
                Target.create("+# to Dexterity", values)

    def test_generated_template(self):
        self.assertEqual(template_from_text("+4.99% to Critical Hit Chance"), "+#% to Critical Hit Chance")
        self.assertEqual(template_from_text("Adds 10 to 20 Physical Damage"), "Adds # to # Physical Damage")


if __name__ == "__main__":
    unittest.main()
