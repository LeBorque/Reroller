from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import unittest

from reroller.catalog import Catalog, search_entries
from reroller.demo import BLIGHT_WEAVER
from reroller.domain import parse_item, Target, RerollError
from scripts.import_catalog import ModifierHTML, normalize_category


class ImportTests(unittest.TestCase):
    def test_html_numeric_spans_keep_fixed_condition_numbers(self):
        template, values, supported = ModifierHTML.parse('Gain <span class="mod-value">(5<span class="ndash">—</span>10)</span>% of Damage as Extra Fire Damage for 4 seconds<br>Every 2 hits, gain <span class="mod-value">+3</span> Rage')
        self.assertEqual(template, 'Gain #% of Damage as Extra Fire Damage for 4 seconds\nEvery 2 hits, gain +# Rage')
        self.assertEqual(values, [['5', '10'], ['3', '3']])
        self.assertTrue(supported)

    def test_negative_and_decimal_values(self):
        template, values, supported = ModifierHTML.parse('<span class="mod-value">-(1.5—2.5)</span>% Damage &amp; <span class="mod-value">+4.99</span>% Crit')
        self.assertEqual(template, '#% Damage & +#% Crit')
        self.assertEqual(values, [['-2.5', '-1.5'], ['4.99', '4.99']])
        self.assertTrue(supported)

    def test_unrecognized_value_is_preserved_and_not_enabled(self):
        template, values, supported = ModifierHTML.parse('<span class="mod-value">unknown value</span> Test')
        self.assertFalse(supported)
        self.assertEqual(template, 'unknown value Test')

    def test_tiers_group_but_sources_stay_distinct(self):
        row = {'Name': 'first', 'Level': '1', 'DropChance': '100', 'ModGenerationTypeID': '2', 'ModFamilyList': ['Family'], 'str': '<span class="mod-value">+2</span> to Test'}
        raw = {'url': 'https://poe2db.tw/us/Test', 'date': '2026-10-19', 'evidence_id': 'fixture', 'data': {
            'baseitem': {'link_name': 'Test', 'cn': 'Test'}, 'config': {}, 'normal': [row, dict(row, Name='second', Level='10', str='<span class="mod-value">+5</span> to Test')], 'essence': [dict(row, DropChance=0)], 'ids': [1, 2]}}
        category, manifest = normalize_category(raw, 'Test')
        self.assertEqual(manifest['records'], 3)
        self.assertEqual(len(category['modifiers']), 2)
        self.assertEqual(len(next(m for m in category['modifiers'] if m['source'] == 'normal')['tiers']), 2)


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog.load()
        cls.item = parse_item(BLIGHT_WEAVER)

    def melee(self):
        return next(m for m in self.catalog.categories['Quarterstaves'].modifiers if m.chaos and m.template == '+# to Level of all Melee Skills')

    def test_complete_index_coverage_and_no_silent_skips(self):
        manifest = self.catalog.manifest
        self.assertTrue(self.catalog.complete)
        self.assertEqual(len(self.catalog.categories), 81)
        self.assertEqual(manifest['missing_categories'], [])
        self.assertEqual(set(manifest['expected_categories']), set(manifest['sources']))
        self.assertEqual(sum(s['records'] for s in manifest['sources'].values()), manifest['records'])
        self.assertEqual(manifest['records'], 24575)
        self.assertEqual(len(self.catalog.modifiers), manifest['choices'])
        self.assertEqual(sum(s['unsupported_records'] for s in manifest['sources'].values()), 0)

    def test_runtime_catalog_has_no_external_brand_or_links(self):
        import gzip
        with gzip.open('reroller/data/catalog.json.gz', 'rt', encoding='utf-8') as stream:
            self.assertNotIn('poe2db', stream.read().casefold())

    def test_captured_source_digests_and_counts(self):
        for identifier, source in self.catalog.manifest['sources'].items():
            path = Path('artifacts/poe2db/raw') / (identifier + '.json')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source['sha256'])
            raw = json.loads(path.read_text(encoding='utf-8'))['data']
            self.assertEqual(source['records'], sum(len(raw[k]) for k in source['groups']))
            self.assertTrue(source['evidence_id'].startswith('ev_'))

    def test_every_numeric_position_has_tier_bounds(self):
        for modifier in self.catalog.modifiers.values():
            self.assertTrue(modifier.supported)
            self.assertNotIn('<span', modifier.template)
            for tier in modifier.tiers:
                self.assertEqual(modifier.template.count('#'), len(tier['values']), modifier.id)
                for low, high in tier['values']:
                    self.assertLessEqual(Decimal(low), Decimal(high))

    def test_quarterstaff_melee_collapses_four_tiers(self):
        modifier = self.melee()
        self.assertEqual([t['level'] for t in modifier.tiers], [18, 36, 55, 81])
        self.catalog.validate('Quarterstaves', modifier.id, self.item, Target.create(modifier.template, ['5']))

    def test_low_level_and_unreachable_threshold_rejected(self):
        modifier = self.melee()
        for item, value in ((replace(self.item, level=80), '5'), (self.item, '6')):
            with self.assertRaises(RerollError) as caught:
                self.catalog.validate('Quarterstaves', modifier.id, item, Target.create(modifier.template, [value]))
            self.assertEqual(caught.exception.message.key, 'modifier_values')

    def test_wrong_category_and_stale_modifier_id_rejected(self):
        modifier = self.melee()
        for category in ('Rings', 'not-a-category'):
            with self.assertRaises(RerollError):
                self.catalog.validate(category, modifier.id, self.item, Target.create(modifier.template, ['5']))
        with self.assertRaises(RerollError):
            self.catalog.validate('Quarterstaves', 'not-a-modifier', self.item, Target.create(modifier.template, ['5']))

    def test_fracture_conflict_but_already_matched_is_zero_currency(self):
        modifier = next(m for m in self.catalog.categories['Quarterstaves'].modifiers if m.chaos and m.template == '+#% to Critical Hit Chance')
        self.catalog.validate('Quarterstaves', modifier.id, self.item, Target.create(modifier.template, ['4.99']))
        with self.assertRaises(RerollError) as caught:
            self.catalog.validate('Quarterstaves', modifier.id, self.item, Target.create(modifier.template, ['5']))
        self.assertEqual(caught.exception.message.key, 'modifier_fracture_conflict')

    def test_exclusive_special_source_not_a_chaos_goal(self):
        modifier = next(m for m in self.catalog.categories['Quarterstaves'].modifiers
                        if m.source == 'desecrated' and not self.catalog.chaos_alternatives(m))
        with self.assertRaises(RerollError) as caught:
            self.catalog.validate('Quarterstaves', modifier.id, self.item, Target.create(modifier.template, ['1'] * modifier.template.count('#')))
        self.assertEqual(caught.exception.message.key, 'modifier_not_chaos')

    def test_special_source_with_regular_equivalent_uses_regular_tiers(self):
        modifier = next(m for m in self.catalog.categories['Quarterstaves'].modifiers
                        if m.source == 'essence' and self.catalog.chaos_alternatives(m) and 'Critical' not in m.template)
        normal = self.catalog.chaos_alternatives(modifier)[0]
        values = [v[0] for v in normal.available_tiers(86)[0]['values']]
        self.catalog.validate('Quarterstaves', modifier.id, self.item, Target.create(modifier.template, values))

    def test_automatic_category_and_armor_subtype(self):
        self.assertEqual(self.catalog.infer(self.item), 'Quarterstaves')
        helmet = replace(self.item, item_class='Helmets', base='Shabby Hood')
        self.assertEqual(self.catalog.infer(helmet), 'Helmets_dex')
        self.assertIsNone(self.catalog.infer(replace(helmet, base='Unknown Helmet')))

    def test_custom_target_still_checks_category(self):
        self.catalog.validate('Quarterstaves', None, self.item, Target.create('+# to Dexterity', ['30']))
        with self.assertRaises(RerollError):
            self.catalog.validate('Rings', None, self.item, Target.create('+# to Dexterity', ['30']))

    def test_search_is_case_insensitive_and_all_words_must_match(self):
        entries = [('a', '+# to Level of all Melee Skills'), ('b', '#% increased Melee Damage')]
        self.assertEqual(search_entries(entries, 'MELEE level'), [entries[0]])


if __name__ == '__main__':
    unittest.main()
