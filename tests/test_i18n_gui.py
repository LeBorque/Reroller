# Python 3.14 | tests/test_i18n_gui.py | Windows 11 offline GUI regression tests
from dataclasses import replace
import json
from pathlib import Path
import socket
from string import Formatter
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from reroller.catalog import Catalog
from reroller.demo import BLIGHT_WEAVER
from reroller.domain import RerollError, Target, parse_item
from reroller.engine import Engine
from reroller.gui import App
from reroller.i18n import MESSAGES, category_label, msg
from reroller.settings import migrate_settings, save_settings, load_settings
from tests.test_engine import FakeConnection


class TranslationTests(unittest.TestCase):
    def test_every_message_has_both_languages_and_identical_parameters(self):
        formatter = Formatter()
        for key, pair in MESSAGES.items():
            with self.subTest(key=key):
                self.assertEqual(len(pair), 2)
                self.assertTrue(all(pair))
                self.assertEqual({p for _, p, _, _ in formatter.parse(pair[0]) if p},
                                 {p for _, p, _, _ in formatter.parse(pair[1]) if p})

    def test_nested_backend_errors_translate(self):
        message = msg('copy_timeout', position=msg('item_position'))
        self.assertNotEqual(message.text('sv-SE'), message.text('en-US'))
        self.assertIn('item', message.text('en-US').lower())

    def test_legacy_settings_keep_custom_target(self):
        old = {'template': 'Adds # to # Fire Damage', 'minimums': ['7', '14'],
               'calibration': {'bounds': [0, 0, 3440, 1440], 'item': [443, 607], 'currency': [84, 624]}}
        result = migrate_settings(old)
        self.assertEqual(result['language'], 'sv-SE')
        self.assertIsNone(result['modifier_id'])
        for key in old:
            self.assertEqual(old[key], result[key])
        self.assertEqual(migrate_settings({'language': 'invalid'})['language'], 'sv-SE')

    def test_settings_roundtrip_stable_ids(self):
        with tempfile.TemporaryDirectory() as folder, patch('reroller.settings.data_directory', return_value=Path(folder)):
            save_settings(None, '+# to Test', ['5'], language='en-US', category_id='Quarterstaves', modifier_id='stable')
            result = load_settings()
            self.assertEqual((result['language'], result['category_id'], result['modifier_id']), ('en-US', 'Quarterstaves', 'stable'))

    def test_all_categories_keep_english_labels_in_swedish(self):
        catalog = Catalog.load()
        for category in catalog.categories.values():
            self.assertEqual(category_label(category.label, 'sv-SE'), category_label(category.label, 'en-US'))


class EngineCatalogTests(unittest.TestCase):
    def test_fresh_item_validation_blocks_before_currency_or_click(self):
        stop = threading.Event()
        connection = FakeConnection(stop)
        def reject(item):
            raise RerollError('category_mismatch')
        result = Engine(connection, Target.create('+# to Level of all Melee Skills', ['5']), 20, stop,
                        clock=lambda: connection.time, validate_target=reject).run()
        self.assertEqual(result.message.key, 'category_mismatch')
        self.assertEqual((connection.clicks, connection.total_currency_reads), (0, 0))

    def test_existing_target_precedes_eligibility_check(self):
        stop = threading.Event()
        connection = FakeConnection(stop)
        connection.initial_target = True
        def reject(item):
            raise AssertionError('Already-matched goals must not need crafting eligibility')
        result = Engine(connection, Target.create('+# to Level of all Melee Skills', ['5']), 20, stop,
                        clock=lambda: connection.time, validate_target=reject).run()
        self.assertTrue(result.matched)
        self.assertEqual(connection.clicks, 0)


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.keys = patch('reroller.gui.Hotkeys').start()
        self.keys.return_value.stop_available = True
        self.keys.return_value.repeat_stop_available = True
        self.keys.return_value.poll.return_value = []
        self.network = patch.object(socket, 'socket', side_effect=AssertionError('No network allowed')).start()
        self.real_connection = patch('reroller.gui.WindowsConnection', side_effect=AssertionError('No game input allowed')).start()
        self.root = tk.Tk()
        self.app = App(self.root, demo=True)
        self.root.update()
        self.root.focus_force()
        self.root.update()

    def tearDown(self):
        self.app.stop.set()
        if self.app.worker:
            self.app.worker.join(5)
        for identifier in self.root.tk.splitlist(self.root.tk.call('after', 'info')):
            self.root.after_cancel(identifier)
        self.app.category_combo.close_popup()
        self.app.target_combo.close_popup()
        self.app.language_combo.close_popup()
        self.root.destroy()
        patch.stopall()

    def choose_melee(self):
        app = self.app
        modifier = next(m for m in app.catalog.categories['Quarterstaves'].modifiers if m.chaos and m.template == '+# to Level of all Melee Skills')
        app.select_modifier(modifier.id)
        app.minimums[0].set('5')
        return modifier

    def state(self):
        app = self.app
        return (app.category_id, app.modifier_id, app.template.get(), tuple(v.get() for v in app.minimums),
                app.budget.get(), app.repeat_mode.get(), app.item, app.calibration)

    def test_language_preserves_all_work_and_half_width_layout(self):
        app = self.app
        self.choose_melee()
        app.budget.set('20')
        app.repeat_mode.set(True)
        before = self.state()
        entries = self.app.category_combo.entries.copy()
        groups = self.app.category_combo.groups.copy()
        for language in ('en-US', 'sv-SE'):
            app.change_language(language)
            self.root.update()
            self.assertEqual(before, self.state())
            self.assertEqual(entries, app.category_combo.entries)
            self.assertEqual(groups, app.category_combo.groups)
            self.assertEqual(app.description.get(), '+# to Level of all Melee Skills')
        widths = [app.category_combo.winfo_width(), app.target_combo.winfo_width()]
        self.assertGreater(min(widths), 200)
        self.assertLessEqual(abs(widths[0] - widths[1]), 1)

    def test_category_change_clears_incompatible_catalog_goal(self):
        app = self.app
        self.choose_melee()
        app.select_category('Rings')
        self.assertIsNone(app.modifier_id)
        self.assertEqual(app.template.get(), '')
        self.assertEqual(len(app.minimums), 0)
        self.assertTrue(all(m.category_id == 'Rings' for m in app.catalog.categories['Rings'].modifiers))

    def test_ambiguous_read_requires_choice_and_clears_stale_id(self):
        self.choose_melee()
        self.app.show_item(replace(self.app.item, item_class='Helmets', base='Unknown Helmet'))
        self.assertIsNone(self.app.category_id)
        self.assertIsNone(self.app.modifier_id)
        self.assertEqual(str(self.app.go_button.cget('state')), 'disabled')

    def test_unavailable_goal_and_level_block_go(self):
        app = self.app
        modifier = next(m for m in app.catalog.categories['Quarterstaves'].modifiers if not m.chaos and not app.catalog.chaos_alternatives(m))
        app.select_modifier(modifier.id)
        self.assertEqual(str(app.go_button.cget('state')), 'disabled')
        self.choose_melee()
        app.show_item(replace(app.item, level=80))
        self.assertEqual(str(app.go_button.cget('state')), 'disabled')
        app.change_language('en-US')
        self.assertIn('80', app.eligibility.get())

    def test_controls_locked_during_run(self):
        app = self.app
        before = self.state()
        app._set_running(True)
        app.change_language('en-US')
        app.select_category('Rings')
        self.assertEqual(app.language, 'sv-SE')
        self.assertEqual(before, self.state())
        self.assertTrue(app.category_combo.disabled)
        self.assertTrue(app.target_combo.disabled)
        self.assertTrue(app.language_combo.disabled)

    def test_flag_language_dropdown_changes_language_without_losing_work(self):
        app = self.app
        self.choose_melee()
        before = self.state()
        combo = app.language_combo
        combo.open()
        self.root.update()
        choices = [w for w in combo.popup.winfo_children() if isinstance(w, tk.Button)]
        self.assertEqual([w.cget('text').strip() for w in choices], ['SE', 'US'])
        self.assertTrue(all(w.cget('image') for w in choices))
        choices[1].invoke()
        self.root.update()
        self.assertEqual(app.language, 'en-US')
        self.assertIn('US', combo.button.cget('text'))
        self.assertIsNone(combo.popup)
        self.assertEqual(before, self.state())
        combo.open()
        self.root.update()
        combo.popup.event_generate('<Up>')
        self.root.update()
        combo.popup.focus_get().event_generate('<Return>')
        self.root.update()
        self.assertEqual(app.language, 'sv-SE')
        self.assertEqual(before, self.state())
        app._set_running(True)
        combo.open()
        combo.choose('en-US')
        self.assertIsNone(combo.popup)
        self.assertEqual(app.language, 'sv-SE')

    def test_custom_goal_and_long_multiline_description(self):
        app = self.app
        app.select_modifier('custom')
        app.template.set('Custom # for 4 seconds')
        app._custom_changed()
        app.minimums[0].set('6')
        before = self.state()
        app.change_language('en-US')
        self.assertEqual(before, self.state())
        multiline = next(m for m in app.catalog.categories['Quarterstaves'].modifiers if '\n' in m.template)
        app.select_modifier(multiline.id)
        self.assertEqual(app.description.get(), multiline.template)

    def test_search_popup_filters_and_selects_catalog_goal(self):
        combo = self.app.target_combo
        combo.open()
        self.root.update()
        search = next(w for w in combo.popup.winfo_children() if isinstance(w, ttk.Entry))
        search.insert(0, 'Melee Skills')
        self.root.update()
        search.event_generate('<Return>')
        self.root.update()
        self.assertIsNone(combo.popup)
        self.assertEqual(self.app.catalog.modifiers[self.app.modifier_id].template, '+# to Level of all Melee Skills')
        combo.open()
        self.root.update()
        self.assertTrue(combo.popup.winfo_viewable())

    def test_only_base_affixes_for_selected_category_in_grouped_list(self):
        app = self.app
        for category in app.catalog.categories.values():
            app.select_category(category.id)
            identifiers = {identifier for identifier, _ in app.target_combo.entries if identifier != 'custom'}
            self.assertEqual(identifiers, {m.id for m in category.modifiers if m.chaos})
            for identifier in identifiers:
                modifier = app.catalog.modifiers[identifier]
                self.assertEqual(modifier.category_id, category.id)
                self.assertEqual(app.target_combo.groups[identifier], 'Base Prefixes' if modifier.generation == 1 else 'Base Suffixes')
        self.assertEqual(len(app.category_combo.groups), 81)
        self.assertEqual(len(set(app.category_combo.groups.values())), 9)

    def test_dropdown_headings_are_bold_and_cannot_be_chosen(self):
        combo = self.app.target_combo
        combo.open()
        self.root.update()
        frame = next(w for w in combo.popup.winfo_children() if isinstance(w, ttk.Frame))
        tree = next(w for w in frame.winfo_children() if isinstance(w, ttk.Treeview))
        headings = [row for row in tree.get_children() if 'heading' in tree.item(row, 'tags')]
        self.assertEqual([tree.item(row, 'text') for row in headings], ['Base Prefixes', 'Base Suffixes'])
        self.assertIn('bold', str(tree.tag_configure('heading', 'font')))
        before = self.state()
        tree.selection_set(headings[0])
        tree.focus_set()
        tree.event_generate('<Return>')
        self.root.update()
        self.assertEqual(before, self.state())
        self.assertIsNotNone(combo.popup)
        tree.event_generate('<Down>')
        tree.event_generate('<Return>')
        self.root.update()
        self.assertIsNone(combo.popup)

    def test_footer_remains_visible_in_custom_mode_and_details_close(self):
        app = self.app
        self.root.update()
        self.assertLessEqual(app.footer.winfo_rooty() + app.footer.winfo_height(), self.root.winfo_rooty() + self.root.winfo_height())
        self.choose_melee()
        app.catalog_details()
        self.root.update()
        dialog = next(w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel))
        dialog.event_generate('<Escape>')
        self.root.update()
        self.assertFalse(dialog.winfo_exists())

    def test_calibration_image_localized_link_and_visible_close(self):
        app = self.app
        before = self.state()
        for language, label in [('en-US', '[SEE HOW]'), ('sv-SE', '[SE HUR]')]:
            app.change_language(language)
            self.assertEqual(app.see_how_button.cget('text'), label)
            app.see_how_button.invoke()
            self.root.update()
            popup = app.calibration_popup
            self.assertEqual((popup.image.width(), popup.image.height()), (828, 832))
            self.assertIs(popup.grab_current(), popup)
            toolbar = next(w for w in popup.winfo_children() if isinstance(w, tk.Frame))
            close = next(w for w in toolbar.winfo_children() if isinstance(w, tk.Button))
            self.assertIn('✕', close.cget('text'))
            close.invoke()
            self.root.update()
            self.assertIsNone(app.calibration_popup)
            self.assertEqual(before, self.state())
        app.show_calibration_image()
        self.root.update()
        app.calibration_popup.event_generate('<Escape>')
        self.root.update()
        self.assertIsNone(app.calibration_popup)

    def test_shortcuts_are_localized_and_external_labels_absent(self):
        def widgets(parent):
            for child in parent.winfo_children():
                yield child
                yield from widgets(child)
        for language, title in [('sv-SE', 'KORTKOMMANDON'), ('en-US', 'KEYBOARD SHORTCUTS')]:
            self.app.change_language(language)
            texts = [str(w.cget('text')) for w in widgets(self.root) if 'text' in w.keys()]
            self.assertIn(title, texts)
            for keys in ['F6', 'F7', 'F8 / Shift+F8', 'Ctrl+Alt+C', 'Esc', '↑ ↓ / Enter', 'Tab / Shift+Tab', 'Space', 'Alt+F4']:
                self.assertIn(keys, texts)
            self.assertNotIn('poe2db', ' '.join(texts).casefold())

    def test_catalog_goal_simulated_run_stops_at_hit(self):
        app = self.app
        self.choose_melee()
        app.repeat_mode.set(False)
        app.budget.set('20')
        app.go()
        deadline = time.monotonic() + 8
        while app.running and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.01)
        self.assertFalse(app.running)
        self.assertIsNotNone(app.last_result)
        self.assertTrue(app.last_result.matched)
        self.assertEqual(app.last_result.attempts, 2)
        self.assertEqual(app.last_result.message.key, 'matched')
        self.real_connection.assert_not_called()


if __name__ == '__main__':
    unittest.main()
