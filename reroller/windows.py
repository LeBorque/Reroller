# Python 3.14 | reroller/windows.py | Windows 11 x64, user32 clipboard and input
from __future__ import annotations

import ctypes as c
from ctypes import wintypes as w
from dataclasses import dataclass
from pathlib import Path
import threading
import time
import queue

from .domain import Item, RerollError, parse_item, parse_chaos_count
from .engine import Cancelled
from .i18n import msg

user32 = c.WinDLL("user32", use_last_error=True)
kernel32 = c.WinDLL("kernel32", use_last_error=True)
ULONG_PTR = c.c_size_t


class MouseInput(c.Structure):
    _fields_ = [("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD),
                ("dwFlags", w.DWORD), ("time", w.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KeyboardInput(c.Structure):
    _fields_ = [("wVk", w.WORD), ("wScan", w.WORD), ("dwFlags", w.DWORD),
                ("time", w.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HardwareInput(c.Structure):
    _fields_ = [("uMsg", w.DWORD), ("wParamL", w.WORD), ("wParamH", w.WORD)]


class InputUnion(c.Union):
    _fields_ = [("mi", MouseInput), ("ki", KeyboardInput), ("hi", HardwareInput)]


class Input(c.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", w.DWORD), ("data", InputUnion)]


def api(dll, name, args, result):
    function = getattr(dll, name)
    function.argtypes, function.restype = args, result
    return function


APP_USER_MODEL_ID = "Zyon.PoE2Reroller"


def set_app_identity():
    shell32 = c.WinDLL("shell32")
    set_identity = api(shell32, "SetCurrentProcessExplicitAppUserModelID", [w.LPCWSTR], c.c_long)
    if set_identity(APP_USER_MODEL_ID) < 0:
        raise OSError("Could not set the Windows application identity")


def icon_diagnostics(root):
    window = GetAncestor(root.winfo_id(), 2)
    send = api(user32, "SendMessageW", [w.HWND, w.UINT, c.c_size_t, c.c_ssize_t], c.c_ssize_t)
    shell32 = c.WinDLL("shell32")
    identity = c.c_wchar_p()
    get_identity = api(shell32, "GetCurrentProcessExplicitAppUserModelID", [c.POINTER(c.c_wchar_p)], c.c_long)
    result = get_identity(c.byref(identity))
    app_id = identity.value if result >= 0 else None
    if identity:
        api(c.WinDLL("ole32"), "CoTaskMemFree", [c.c_void_p], None)(c.cast(identity, c.c_void_p))
    return {"application_id": app_id,
            "small_icon": int(send(window, 0x007F, 0, 0)),
            "taskbar_icon": int(send(window, 0x007F, 1, 0))}


GetForegroundWindow = api(user32, "GetForegroundWindow", [], w.HWND)
GetClientRect = api(user32, "GetClientRect", [w.HWND, c.POINTER(w.RECT)], w.BOOL)
ClientToScreen = api(user32, "ClientToScreen", [w.HWND, c.POINTER(w.POINT)], w.BOOL)
GetCursorPos = api(user32, "GetCursorPos", [c.POINTER(w.POINT)], w.BOOL)
SetCursorPos = api(user32, "SetCursorPos", [c.c_int, c.c_int], w.BOOL)
GetAsyncKeyState = api(user32, "GetAsyncKeyState", [c.c_int], c.c_short)
SendInput = api(user32, "SendInput", [w.UINT, c.POINTER(Input), c.c_int], w.UINT)
GetAncestor = api(user32, "GetAncestor", [w.HWND, w.UINT], w.HWND)
WindowFromPoint = api(user32, "WindowFromPoint", [w.POINT], w.HWND)
IsWindow = api(user32, "IsWindow", [w.HWND], w.BOOL)
IsWindowVisible = api(user32, "IsWindowVisible", [w.HWND], w.BOOL)
IsIconic = api(user32, "IsIconic", [w.HWND], w.BOOL)
ShowWindow = api(user32, "ShowWindow", [w.HWND, c.c_int], w.BOOL)
SetForegroundWindow = api(user32, "SetForegroundWindow", [w.HWND], w.BOOL)
GetWindowTextW = api(user32, "GetWindowTextW", [w.HWND, w.LPWSTR, c.c_int], c.c_int)
GetWindowThreadProcessId = api(user32, "GetWindowThreadProcessId", [w.HWND, c.POINTER(w.DWORD)], w.DWORD)
OpenProcess = api(kernel32, "OpenProcess", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE)
CloseHandle = api(kernel32, "CloseHandle", [w.HANDLE], w.BOOL)
QueryFullProcessImageNameW = api(kernel32, "QueryFullProcessImageNameW", [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)], w.BOOL)
OpenClipboard = api(user32, "OpenClipboard", [w.HWND], w.BOOL)
CloseClipboard = api(user32, "CloseClipboard", [], w.BOOL)
EmptyClipboard = api(user32, "EmptyClipboard", [], w.BOOL)
GetClipboardData = api(user32, "GetClipboardData", [w.UINT], w.HANDLE)
GetClipboardSequenceNumber = api(user32, "GetClipboardSequenceNumber", [], w.DWORD)
GlobalLock = api(kernel32, "GlobalLock", [w.HGLOBAL], c.c_void_p)
GlobalUnlock = api(kernel32, "GlobalUnlock", [w.HGLOBAL], w.BOOL)
CreateWindowExW = api(user32, "CreateWindowExW", [w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD,
                        c.c_int, c.c_int, c.c_int, c.c_int, w.HWND, w.HMENU, w.HINSTANCE, c.c_void_p], w.HWND)
DestroyWindow = api(user32, "DestroyWindow", [w.HWND], w.BOOL)
AddClipboardFormatListener = api(user32, "AddClipboardFormatListener", [w.HWND], w.BOOL)
RemoveClipboardFormatListener = api(user32, "RemoveClipboardFormatListener", [w.HWND], w.BOOL)
PeekMessageW = api(user32, "PeekMessageW", [c.POINTER(w.MSG), w.HWND, w.UINT, w.UINT, w.UINT], w.BOOL)
TranslateMessage = api(user32, "TranslateMessage", [c.POINTER(w.MSG)], w.BOOL)
DispatchMessageW = api(user32, "DispatchMessageW", [c.POINTER(w.MSG)], c.c_ssize_t)
MsgWaitForMultipleObjects = api(user32, "MsgWaitForMultipleObjects", [w.DWORD, c.c_void_p, w.BOOL, w.DWORD, w.DWORD], w.DWORD)
RegisterHotKey = api(user32, "RegisterHotKey", [w.HWND, c.c_int, w.UINT, w.UINT], w.BOOL)
UnregisterHotKey = api(user32, "UnregisterHotKey", [w.HWND, c.c_int], w.BOOL)
GetMessageW = api(user32, "GetMessageW", [c.POINTER(w.MSG), w.HWND, w.UINT, w.UINT], w.BOOL)
PostThreadMessageW = api(user32, "PostThreadMessageW", [w.DWORD, w.UINT, w.WPARAM, w.LPARAM], w.BOOL)
GetCurrentThreadId = api(kernel32, "GetCurrentThreadId", [], w.DWORD)
EnumProc = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
EnumWindows = api(user32, "EnumWindows", [EnumProc, w.LPARAM], w.BOOL)


def dpi_aware() -> None:
    try:
        api(user32, "SetProcessDpiAwarenessContext", [c.c_void_p], w.BOOL)(c.c_void_p(-4))
    except AttributeError:
        user32.SetProcessDPIAware()


def executable(hwnd: int) -> str:
    pid = w.DWORD()
    GetWindowThreadProcessId(hwnd, c.byref(pid))
    process = OpenProcess(0x1000, False, pid.value)
    if not process:
        return ""
    try:
        buf, size = c.create_unicode_buffer(32768), w.DWORD(32768)
        return buf.value if QueryFullProcessImageNameW(process, 0, buf, c.byref(size)) else ""
    finally:
        CloseHandle(process)


def game_windows() -> list[int]:
    found = []

    @EnumProc
    def visit(hwnd, _):
        title = c.create_unicode_buffer(512)
        GetWindowTextW(hwnd, title, len(title))
        if IsWindowVisible(hwnd) and title.value == "Path of Exile 2":
            if Path(executable(hwnd)).name.lower() in {"pathofexilesteam.exe", "pathofexile.exe", "pathofexile_x64.exe"}:
                found.append(hwnd)
        return True

    EnumWindows(visit, 0)
    return found


def geometry(hwnd: int) -> tuple[int, int, int, int]:
    rect, origin = w.RECT(), w.POINT(0, 0)
    if not GetClientRect(hwnd, c.byref(rect)) or not ClientToScreen(hwnd, c.byref(origin)):
        raise RerollError(msg('window_unreadable'))
    return origin.x, origin.y, rect.right, rect.bottom


@dataclass(frozen=True)
class Calibration:
    bounds: tuple[int, int, int, int]
    currency: tuple[int, int] | None = None
    item: tuple[int, int] | None = None

    def validate(self) -> None:
        if len(self.bounds) != 4 or any(type(n) is not int for n in self.bounds):
            raise RerollError(msg('calibration_invalid'))
        if self.bounds[2] < 100 or self.bounds[3] < 100:
            raise RerollError(msg('window_small'))
        for point in (self.currency, self.item):
            if point is not None and (len(point) != 2 or any(type(n) is not int for n in point)
                                      or not (0 <= point[0] < self.bounds[2] and 0 <= point[1] < self.bounds[3])):
                raise RerollError(msg('point_outside'))
        if self.currency is not None and self.currency == self.item:
            raise RerollError(msg('points_same'))


def capture_point() -> tuple[tuple[int, int, int, int], tuple[int, int]]:
    hwnd = GetForegroundWindow()
    if hwnd not in game_windows():
        raise RerollError(msg('activate_to_calibrate'))
    bounds = geometry(hwnd)
    point = w.POINT()
    if not GetCursorPos(c.byref(point)):
        raise RerollError(msg('pointer_unreadable'))
    relative = point.x - bounds[0], point.y - bounds[1]
    Calibration(bounds, item=relative).validate()
    return bounds, relative


class Hotkeys:
    def __init__(self, stop: threading.Event | None = None):
        self.keys: dict[int, str] = {}
        self.events: queue.Queue[str] = queue.Queue()
        self.stop = stop
        self.ready = threading.Event()
        self.thread_id = 0
        self.thread = threading.Thread(target=self._listen, name="reroller-hotkeys", daemon=True)
        self.thread.start()
        if not self.ready.wait(2):
            raise RerollError(msg('hotkeys_failed'))
        self.stop_available = 0x4A12 in self.keys
        self.repeat_stop_available = 0x4A13 in self.keys

    def _listen(self):
        self.thread_id = GetCurrentThreadId()
        msg = w.MSG()
        # Create this thread's queue before exposing its ID. Tk must never own these messages.
        PeekMessageW(c.byref(msg), None, 0, 0, 0)
        try:
            for identifier, key, name in ((0x4A10, 0x75, "currency"), (0x4A11, 0x76, "item"), (0x4A12, 0x77, "stop"), (0x4A13, 0x77, "stop")):
                modifiers = 0x4004 if identifier == 0x4A13 else 0x4000
                if RegisterHotKey(None, identifier, modifiers, key):
                    self.keys[identifier] = name
            self.ready.set()
            while GetMessageW(c.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x312 and msg.wParam in self.keys:
                    name = self.keys[msg.wParam]
                    if name == "stop" and self.stop is not None:
                        self.stop.set()
                    self.events.put(name)
        finally:
            for identifier in self.keys:
                UnregisterHotKey(None, identifier)
            self.ready.set()

    def poll(self) -> list[str]:
        result = []
        try:
            while True:
                result.append(self.events.get_nowait())
        except queue.Empty:
            pass
        return result

    def close(self) -> None:
        if self.thread.is_alive():
            PostThreadMessageW(self.thread_id, 0x12, 0, 0)
            self.thread.join(timeout=1)
        self.keys.clear()


class Clipboard:
    """Thread-owned message-only window; WM_CLIPBOARDUPDATE wakes the copy wait."""

    def __init__(self):
        self.hwnd = CreateWindowExW(0, "STATIC", "PoE2RerollerClipboard", 0, 0, 0, 0, 0,
                                    c.c_void_p(-3), None, None, None)
        if not self.hwnd:
            raise RerollError(msg('clipboard_window_failed'))
        if not AddClipboardFormatListener(self.hwnd):
            DestroyWindow(self.hwnd)
            self.hwnd = None
            raise RerollError(msg('clipboard_listener_failed'))

    def pump(self, milliseconds: int = 10) -> None:
        MsgWaitForMultipleObjects(0, None, False, milliseconds, 0x4FF)
        msg = w.MSG()
        while PeekMessageW(c.byref(msg), self.hwnd, 0, 0, 1):
            TranslateMessage(c.byref(msg))
            DispatchMessageW(c.byref(msg))

    def clear(self) -> int:
        if not OpenClipboard(self.hwnd):
            raise RerollError(msg('clipboard_busy'))
        try:
            if not EmptyClipboard():
                raise RerollError(msg('clipboard_clear_failed'))
        finally:
            CloseClipboard()
        return GetClipboardSequenceNumber()

    def text(self) -> str | None:
        if not OpenClipboard(self.hwnd):
            return None
        try:
            handle = GetClipboardData(13)
            if not handle:
                return None
            pointer = GlobalLock(handle)
            if not pointer:
                return None
            try:
                return c.wstring_at(pointer)
            finally:
                GlobalUnlock(handle)
        finally:
            CloseClipboard()

    def close(self) -> None:
        if self.hwnd:
            RemoveClipboardFormatListener(self.hwnd)
            DestroyWindow(self.hwnd)
            self.hwnd = None


class WindowsConnection:
    def __init__(self, calibration: Calibration, stop: threading.Event):
        calibration.validate()
        found = game_windows()
        if len(found) != 1:
            raise RerollError(msg('one_game_required'))
        self.hwnd, self.calibration, self.stop = found[0], calibration, stop
        self.clipboard: Clipboard | None = None
        self.selection_pending = False
        self.shift_owned = False
        self.repeat_active = False
        if IsIconic(self.hwnd):
            ShowWindow(self.hwnd, 9)
        SetForegroundWindow(self.hwnd)
        deadline = time.monotonic() + 1
        while GetForegroundWindow() != self.hwnd and time.monotonic() < deadline:
            if stop.wait(0.02):
                raise Cancelled(msg('stopped'))
        self.guard()
        self.clipboard = Clipboard()

    def guard(self) -> None:
        if self.stop.is_set() or GetAsyncKeyState(0x77) & 0x8000:
            self.stop.set()
            raise Cancelled(msg('stopped_f8'))
        if not IsWindow(self.hwnd) or IsIconic(self.hwnd) or GetForegroundWindow() != self.hwnd:
            raise RerollError(msg('focus_lost'))
        if geometry(self.hwnd) != self.calibration.bounds:
            raise RerollError(msg('geometry_changed'))

    def wait(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.guard()
            self.stop.wait(min(0.01, max(0, deadline - time.monotonic())))

    def clean_keys(self) -> None:
        keys = (0x11, 0x12, 0x01, 0x02) if getattr(self, "shift_owned", False) else (0x10, 0x11, 0x12, 0x01, 0x02)
        if any(GetAsyncKeyState(vk) & 0x8000 for vk in keys):
            raise RerollError(msg('release_keys'))

    def send(self, inputs: list[Input]) -> None:
        self.guard()
        array = (Input * len(inputs))(*inputs)
        if SendInput(len(inputs), array, c.sizeof(Input)) != len(inputs):
            # Release only keys/buttons this program can synthesize; never retry a click.
            release = [self.key(vk, up=True) for vk in (0x43, 0x12, 0x11)]
            if getattr(self, "shift_owned", False):
                release.append(self.key(0xA0, up=True))
                self.shift_owned = False
            release += [Input(type=0, mi=MouseInput(dwFlags=0x04 | 0x10))]
            cleanup = (Input * len(release))(*release)
            SendInput(len(release), cleanup, c.sizeof(Input))
            raise RerollError(msg('input_rejected'))

    @staticmethod
    def key(vk: int, up: bool = False) -> Input:
        return Input(type=1, ki=KeyboardInput(wVk=vk, dwFlags=2 if up else 0))

    def move(self, point: tuple[int, int] | None) -> None:
        self.guard()
        if point is None:
            raise RerollError(msg('calibrate_both'))
        x, y = point[0] + self.calibration.bounds[0], point[1] + self.calibration.bounds[1]
        if GetAncestor(WindowFromPoint(w.POINT(x, y)), 2) != self.hwnd:
            raise RerollError(msg('position_covered'))
        current = w.POINT()
        if GetCursorPos(c.byref(current)) and (current.x, current.y) == (x, y):
            return
        if not SetCursorPos(x, y):
            raise RerollError(msg('pointer_move_failed'))
        self.wait(0.035)

    def confirm_pointer(self, point: tuple[int, int]) -> None:
        current = w.POINT()
        if not GetCursorPos(c.byref(current)):
            raise RerollError(msg('pointer_check_failed'))
        expected = point[0] + self.calibration.bounds[0], point[1] + self.calibration.bounds[1]
        if (current.x, current.y) != expected or GetAncestor(WindowFromPoint(current), 2) != self.hwnd:
            raise RerollError(msg('pointer_changed'))

    def copy_at(self, point: tuple[int, int] | None) -> str:
        label = "item" if point == self.calibration.item else "currency"
        self.move(point)
        self.clean_keys()
        sequence = self.clipboard.clear()
        self.confirm_pointer(point)
        self.copy_shortcut()
        deadline = time.monotonic() + 1
        next_copy = deadline - 1 + 0.15
        while (now := time.monotonic()) < deadline:
            self.guard()
            self.confirm_pointer(point)
            self.clipboard.pump()
            if GetClipboardSequenceNumber() != sequence:
                text = self.clipboard.text()
                if text and text.strip():
                    return text
            if now >= next_copy:
                # Crafting can temporarily ignore a shortcut. Retry copying only; never reapply currency.
                self.clean_keys()
                self.copy_shortcut()
                next_copy = now + 0.15
        raise RerollError("copy_timeout", position=msg("item_position" if label == "item" else "currency_position"))

    def copy_shortcut(self) -> None:
        released = False
        try:
            self.send([self.key(0x11), self.key(0x12)])
            self.wait(0.025)
            self.send([self.key(0x43)])
            self.wait(0.025)
            self.send([self.key(0x43, True), self.key(0x12, True), self.key(0x11, True)])
            released = True
            self.wait(0.025)
        finally:
            if not released:
                # A stop during a chord must release our keys even when guard() rejects further input.
                cleanup = (Input * 3)(self.key(0x43, True), self.key(0x12, True), self.key(0x11, True))
                SendInput(3, cleanup, c.sizeof(Input))

    def read_item(self) -> Item:
        return parse_item(self.copy_at(self.calibration.item))

    def read_currency(self) -> int:
        return parse_chaos_count(self.copy_at(self.calibration.currency))

    def apply_once(self, before_click) -> None:
        if getattr(self, "repeat_active", False):
            self.guard()
            self.clean_keys()
            self.confirm_pointer(self.calibration.item)
            before_click()
            self.send([Input(type=0, mi=MouseInput(dwFlags=0x02)), Input(type=0, mi=MouseInput(dwFlags=0x04))])
            self.wait(0.04)
            return
        self.move(self.calibration.currency)
        self.clean_keys()
        self.confirm_pointer(self.calibration.currency)
        self.selection_pending = True
        self.send([Input(type=0, mi=MouseInput(dwFlags=0x08)), Input(type=0, mi=MouseInput(dwFlags=0x10))])
        self.wait(0.035)
        self.move(self.calibration.item)
        self.clean_keys()
        self.confirm_pointer(self.calibration.item)
        before_click()
        self.send([Input(type=0, mi=MouseInput(dwFlags=0x02)), Input(type=0, mi=MouseInput(dwFlags=0x04))])
        self.selection_pending = False
        # A single application without Shift ends the currency cursor. Escape here would close the stash.
        self.wait(0.04)

    def begin_repeat(self) -> None:
        self.move(self.calibration.currency)
        self.clean_keys()
        self.confirm_pointer(self.calibration.currency)
        self.shift_owned = True
        self.selection_pending = True
        self.send([self.key(0xA0), Input(type=0, mi=MouseInput(dwFlags=0x08)), Input(type=0, mi=MouseInput(dwFlags=0x10))])
        self.wait(0.035)
        self.move(self.calibration.item)
        self.repeat_active = True

    def end_repeat(self) -> None:
        owned = getattr(self, "shift_owned", False)
        self.repeat_active = False
        if owned:
            # Release only our synthetic Shift even on focus loss or F8; guard must not block key-up.
            release = (Input * 1)(self.key(0xA0, up=True))
            if SendInput(1, release, c.sizeof(Input)) != 1:
                raise RerollError(msg('shift_release_failed'))
            self.shift_owned = False
        if owned and IsWindow(self.hwnd) and not IsIconic(self.hwnd) and GetForegroundWindow() == self.hwnd and geometry(self.hwnd) == self.calibration.bounds:
            # Escape cancels the remaining currency cursor; no crafting click is sent.
            # If the stack was depleted it may close the stash instead.
            cancel = (Input * 2)(self.key(0x1B), self.key(0x1B, True))
            if SendInput(2, cancel, c.sizeof(Input)) == 2:
                self.selection_pending = False

    def close(self) -> None:
        try:
            self.end_repeat()
        finally:
            if self.clipboard:
                self.clipboard.close()
