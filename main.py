# Python 3.14 | main.py | Windows 11, run with python main.py
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import threading
import tkinter as tk
import traceback

from reroller.windows import dpi_aware, set_app_identity, icon_diagnostics, APP_USER_MODEL_ID
from reroller.gui import App


def main():
    parser = argparse.ArgumentParser(description="PoE 2 Reroller")
    parser.add_argument("--demo", action="store_true", help="Explicit simulation; never touches the game")
    parser.add_argument("--smoke-test", type=Path, help="Write packaged GUI + simulated engine test result to JSON and exit")
    args = parser.parse_args()
    dpi_aware()
    set_app_identity()
    root = tk.Tk()
    app = App(root, demo=args.demo or args.smoke_test is not None)
    if args.smoke_test:
        from reroller.domain import Target, parse_item
        from reroller.demo import BLIGHT_WEAVER, DemoConnection
        from reroller.engine import Engine
        report = {"gui_created": True, "simulation": True}
        try:
            item = parse_item(BLIGHT_WEAVER)
            assert item.fractures == ("+4.99% to Critical Hit Chance",)
            result = Engine(DemoConnection(threading.Event()),
                            Target.create("+# to Level of all Melee Skills", ["5"]),
                            10, threading.Event()).run()
            assert result.matched and result.attempts == 2
            report.update(ok=True, result=asdict(result))
            report["catalog"] = {"complete": app.catalog.complete, "categories": len(app.catalog.categories), "choices": len(app.catalog.modifiers)}
            state = (app.template.get(), [v.get() for v in app.minimums], app.category_id, app.modifier_id, app.budget.get())
            app.change_language("en-US")
            assert state == (app.template.get(), [v.get() for v in app.minimums], app.category_id, app.modifier_id, app.budget.get())
            assert app.read_button.cget("text") == "Read item · 0 orbs"
            app.change_language("sv-SE")
            report["language_switch_preserved_state"] = True
        except Exception:
            report.update(ok=False, error=traceback.format_exc())
        def finish():
            root.update_idletasks()
            report["windows_icon"] = icon_diagnostics(root)
            if (report["windows_icon"]["application_id"] != APP_USER_MODEL_ID
                    or not report["windows_icon"]["small_icon"] or not report["windows_icon"]["taskbar_icon"]):
                report.update(ok=False, error="Windows title/taskbar icon or application identity is missing")
            report["window_size"] = [root.winfo_width(), root.winfo_height()]
            report["dropdown_widths"] = [app.category_combo.winfo_width(), app.target_combo.winfo_width()]
            if min(report["dropdown_widths"]) < 200 or abs(report["dropdown_widths"][0] - report["dropdown_widths"][1]) > 1:
                report.update(ok=False, error="Dropdown layout was not two equal half-width controls")
            args.smoke_test.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            app.close()
        root.after(500, finish)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        from reroller.settings import data_directory
        report = traceback.format_exc()
        (data_directory() / "startup-error.log").write_text(report, encoding="utf-8")
        import ctypes
        from reroller.i18n import msg
        from reroller.settings import load_settings
        ctypes.windll.user32.MessageBoxW(None, msg("startup_error", path=data_directory()).text(load_settings()["language"]), "PoE 2 Reroller", 0x10)
        sys.exit(1)
