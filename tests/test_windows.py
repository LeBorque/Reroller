import ctypes
from ctypes import wintypes
import threading
import time
import unittest
from unittest.mock import patch, Mock

from reroller.domain import RerollError
from reroller.engine import Cancelled
from reroller import windows as win


BOUNDS = (0, 0, 3440, 1440)


class WindowsTests(unittest.TestCase):
    def test_hotkey_survives_tk_message_loop(self):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        current_thread = win.api(win.kernel32, 'GetCurrentThreadId', [], wintypes.DWORD)
        post = win.api(win.user32, 'PostThreadMessageW', [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM], wintypes.BOOL)
        keys = None
        stop = threading.Event()
        try:
            with patch.object(win, 'RegisterHotKey', return_value=True), patch.object(win, 'UnregisterHotKey', return_value=True):
                keys = win.Hotkeys(stop)
                self.assertTrue(post(getattr(keys, 'thread_id', current_thread()), 0x312, 0x4A11, 0))
                root.update()
                deadline = time.monotonic() + 0.25
                received = []
                while time.monotonic() < deadline and not received:
                    root.update()
                    received.extend(keys.poll())
                    time.sleep(0.005)
                self.assertEqual(received, ['item'])
                self.assertTrue(post(keys.thread_id, 0x312, 0x4A12, 0))
                self.assertTrue(stop.wait(0.25), 'F8 must stop without Tk polling')
                keys.close()
                keys = None
        finally:
            if keys:
                keys.close()
            root.destroy()

    def connection(self):
        connection = win.WindowsConnection.__new__(win.WindowsConnection)
        connection.hwnd = 123
        connection.stop = threading.Event()
        connection.calibration = win.Calibration(BOUNDS, (50, 50), (200, 200))
        connection.selection_pending = False
        connection.clipboard = Mock()
        return connection

    def test_native_input_structure_size(self):
        self.assertEqual(ctypes.sizeof(win.Input), 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)

    def test_repeat_selects_once_then_only_left_clicks(self):
        connection = self.connection()
        sent = []
        with patch.object(connection, 'move') as move, patch.object(connection, 'clean_keys'), \
                patch.object(connection, 'confirm_pointer'), patch.object(connection, 'guard'), \
                patch.object(connection, 'wait'), patch.object(connection, 'send', side_effect=lambda inputs: sent.extend(inputs)):
            connection.begin_repeat()
            connection.apply_once(lambda: None)
            connection.apply_once(lambda: None)
        self.assertEqual(move.call_count, 2)
        self.assertEqual([event.mi.dwFlags for event in sent if event.type == 0], [8, 16, 2, 4, 2, 4])
        self.assertEqual([event.ki.wVk for event in sent if event.type == 1], [0xA0])

    def test_repeat_cleanup_releases_shift_on_focus_loss(self):
        connection = self.connection()
        connection.shift_owned = connection.repeat_active = True
        with patch.object(win, 'SendInput', return_value=1) as send, patch.object(win, 'IsWindow', return_value=True), \
                patch.object(win, 'IsIconic', return_value=False), patch.object(win, 'GetForegroundWindow', return_value=999):
            connection.end_repeat()
        self.assertEqual(send.call_count, 1)
        packet = send.call_args.args[1]
        self.assertEqual((packet[0].ki.wVk, packet[0].ki.dwFlags), (0xA0, 2))
        self.assertFalse(connection.shift_owned)

    def test_repeat_owns_shift_but_rejects_ctrl(self):
        connection = self.connection()
        connection.shift_owned = True
        with patch.object(win, 'GetAsyncKeyState', side_effect=lambda key: 0x8000 if key == 0x10 else 0):
            connection.clean_keys()
        with patch.object(win, 'GetAsyncKeyState', side_effect=lambda key: 0x8000 if key == 0x11 else 0):
            with self.assertRaises(RerollError):
                connection.clean_keys()

    def test_f8_stops_even_without_ui_thread_poll(self):
        connection = self.connection()
        with patch.object(win, 'GetAsyncKeyState', return_value=0x8000):
            with self.assertRaises(Cancelled):
                connection.guard()
        self.assertTrue(connection.stop.is_set())

    def test_focus_loss_and_geometry_change(self):
        for foreground, bounds in ((999, BOUNDS), (123, (1, 0, 3440, 1440))):
            connection = self.connection()
            with self.subTest(foreground=foreground), patch.object(win, 'GetAsyncKeyState', return_value=0), \
                    patch.object(win, 'IsWindow', return_value=True), patch.object(win, 'IsIconic', return_value=False), \
                    patch.object(win, 'GetForegroundWindow', return_value=foreground), patch.object(win, 'geometry', return_value=bounds):
                with self.assertRaises(RerollError):
                    connection.guard()

    def test_no_fresh_clipboard_never_uses_old_text(self):
        connection = self.connection()
        connection.clipboard.clear.return_value = 100
        connection.clipboard.text.return_value = "old text"
        with patch.object(connection, 'move'), patch.object(connection, 'clean_keys'), patch.object(connection, 'confirm_pointer'), \
                patch.object(connection, 'send'), patch.object(connection, 'wait'), patch.object(connection, 'guard'), \
                patch.object(win, 'GetClipboardSequenceNumber', return_value=100), \
                patch.object(win.time, 'monotonic', side_effect=[0, 0, 2]):
            with self.assertRaises(RerollError):
                connection.copy_at((200, 200))
        connection.clipboard.text.assert_not_called()

    def test_fresh_empty_clipboard_rejected(self):
        connection = self.connection()
        connection.clipboard.clear.return_value = 100
        connection.clipboard.text.return_value = ""
        with patch.object(connection, 'move'), patch.object(connection, 'clean_keys'), patch.object(connection, 'confirm_pointer'), \
                patch.object(connection, 'send'), patch.object(connection, 'wait'), patch.object(connection, 'guard'), \
                patch.object(win, 'GetClipboardSequenceNumber', return_value=101), \
                patch.object(win.time, 'monotonic', side_effect=[0, 0, 2]):
            with self.assertRaises(RerollError):
                connection.copy_at((200, 200))

    def test_copy_retries_shortcut_without_any_crafting_click(self):
        connection = self.connection()
        connection.clipboard.clear.return_value = 100
        connection.clipboard.text.return_value = 'fresh item text'
        with patch.object(connection, 'move'), patch.object(connection, 'clean_keys'), patch.object(connection, 'confirm_pointer'), \
                patch.object(connection, 'copy_shortcut') as shortcut, patch.object(connection, 'guard'), \
                patch.object(win, 'GetClipboardSequenceNumber', side_effect=lambda: 101 if shortcut.call_count >= 2 else 100), \
                patch.object(win.time, 'monotonic', side_effect=[0, 0.2, 0.4, 1.2]):
            self.assertEqual(connection.copy_at((200, 200)), 'fresh item text')
        self.assertEqual(shortcut.call_count, 2)

    def test_copy_chord_has_dwell_and_releases_without_shift_up(self):
        connection = self.connection()
        with patch.object(connection, 'send') as send, patch.object(connection, 'wait') as wait:
            connection.copy_shortcut()
        self.assertEqual(wait.call_count, 3)
        packets = [event for call in send.call_args_list for event in call.args[0]]
        self.assertTrue(all(event.type == 1 for event in packets))
        self.assertEqual([event.ki.wVk for event in packets], [0x11, 0x12, 0x43, 0x43, 0x12, 0x11])

    def test_copy_chord_stop_always_releases_ctrl_alt_c(self):
        connection = self.connection()
        with patch.object(connection, 'send'), patch.object(connection, 'wait', side_effect=Cancelled('stop')), \
                patch.object(win, 'SendInput', return_value=3) as cleanup:
            with self.assertRaises(Cancelled):
                connection.copy_shortcut()
        self.assertEqual([event.ki.dwFlags for event in cleanup.call_args.args[1]], [2, 2, 2])

    def test_stop_between_currency_selection_and_item_click(self):
        connection = self.connection()
        sent = []
        with patch.object(connection, 'move'), patch.object(connection, 'clean_keys'), patch.object(connection, 'confirm_pointer'), \
                patch.object(connection, 'wait'), patch.object(connection, 'send', side_effect=lambda events: sent.extend(events)):
            def cancelled():
                raise Cancelled("stop")
            with self.assertRaises(Cancelled):
                connection.apply_once(cancelled)
        self.assertEqual([event.mi.dwFlags for event in sent], [0x08, 0x10])
        self.assertTrue(connection.selection_pending)

    def test_partial_input_failure_is_not_retried(self):
        connection = self.connection()
        with patch.object(connection, 'guard'), patch.object(win, 'SendInput', side_effect=[1, 4]) as send:
            with self.assertRaises(RerollError):
                connection.send([win.Input(type=0, mi=win.MouseInput(dwFlags=0x02)),
                                 win.Input(type=0, mi=win.MouseInput(dwFlags=0x04))])
        self.assertEqual(send.call_count, 2)
        # The only subsequent packet releases held keys/buttons; it contains no mouse-down event.
        release_array = send.call_args_list[1].args[1]
        self.assertEqual(release_array[3].mi.dwFlags, 0x14)

    def test_calibration_rejects_same_or_outside_points(self):
        for calibration in (win.Calibration(BOUNDS, (50, 50), (50, 50)),
                            win.Calibration(BOUNDS, (-1, 0), (50, 50)),
                            win.Calibration(BOUNDS, (3440, 0), (50, 50))):
            with self.subTest(calibration=calibration), self.assertRaises(RerollError):
                calibration.validate()


if __name__ == '__main__':
    unittest.main()
