# Python 3.14 | reroller/gui.py | Windows 11 catalog and bilingual desktop interface
from __future__ import annotations

from dataclasses import replace, asdict
import json
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import winsound

from . import __version__
from .catalog import Catalog
from .domain import Target, Item, RerollError, validate_item, parse_item
from .engine import Engine, Progress
from .i18n import LANGUAGES, Message, msg, category_label
from .settings import data_directory, load_settings, load_calibration, save_settings
from .windows import Calibration, WindowsConnection, Hotkeys, capture_point
from .demo import DemoConnection, BLIGHT_WEAVER
from .widgets import SearchDropdown, LanguageDropdown

BG, PANEL, FIELD, TEXT, MUTED, GOLD, GREEN = "#111820", "#1b2632", "#111c27", "#edf0f2", "#a3b3c3", "#e8bd72", "#83d6b1"


class App:
    def __init__(self, root: tk.Tk, demo: bool = False):
        self.root, self.demo = root, demo
        self.events: queue.Queue = queue.Queue()
        self.stop = threading.Event()
        self.worker: threading.Thread | None = None
        self.closing = self.running = False
        self.item: Item | None = None
        self.calibration_popup = None
        self.last_result = self.last_progress = None
        self.settings = {} if demo else load_settings()
        self.language = self.settings.get("language", "sv-SE")
        self.calibration = None if demo else load_calibration(self.settings)
        self.catalog = Catalog.load()
        self.category_id = self.settings.get("category_id")
        if self.category_id not in self.catalog.categories:
            self.category_id = None
        self.modifier_id = self.settings.get("modifier_id")
        selected = self.catalog.modifiers.get(self.modifier_id)
        if not selected or selected.category_id != self.category_id or not selected.chaos:
            self.modifier_id = None
        self.minimums: list[tk.StringVar] = []
        self.localized_widgets: list[tuple[tk.Widget, str]] = []
        self.log_messages: list[Message] = []
        self.current_status = msg("simulation" if demo else "ready")
        self.hotkeys = Hotkeys(self.stop)
        self.log = logging.getLogger("poe2reroller")
        self.log.setLevel(logging.INFO)
        if not self.log.handlers:
            handler = RotatingFileHandler(data_directory() / "reroller.log", maxBytes=500_000, backupCount=2, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.log.addHandler(handler)
        self._build()
        self._rebuild_minimums(self.settings.get("minimums", ["5"]))
        self._apply_language()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(25, self._pump)
        if demo:
            self.show_item(parse_item(BLIGHT_WEAVER))
        elif not self.hotkeys.stop_available:
            self.set_status(msg("f8_busy"))

    def tr(self, key, **params):
        return msg(key, **params).text(self.language)

    def translated(self, widget, key):
        self.localized_widgets.append((widget, key))
        widget.configure(text=self.tr(key))
        return widget

    def _build(self):
        root = self.root
        root.geometry("980x1060")
        root.minsize(920, 960)
        root.configure(bg=BG)
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "reroller_icon.ico"
        root.iconbitmap(default=str(icon_path))
        root.iconbitmap(str(icon_path))
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background=PANEL, foreground=TEXT)
        style.configure("TFrame", background=PANEL)
        style.configure("Outer.TFrame", background=BG)
        style.configure("TLabel", background=PANEL, foreground=TEXT)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("TLabelframe", background=PANEL, bordercolor="#334354", relief="solid")
        style.configure("TLabelframe.Label", background=PANEL, foreground=GOLD, font=("Segoe UI Semibold", 11))
        style.configure("TButton", padding=(12, 7), background="#304254", foreground=TEXT, borderwidth=0)
        style.map("TButton", background=[("active", "#40596e"), ("disabled", "#202b36")], foreground=[("disabled", "#738392")])
        style.configure("Go.TButton", background=GOLD, foreground=BG, font=("Segoe UI Semibold", 12))
        style.map("Go.TButton", background=[("disabled", "#3b3e3e"), ("active", "#ffcf82")], foreground=[("disabled", "#8c949a")])
        style.configure("Shift.TCheckbutton", background=PANEL, foreground=TEXT, padding=(8, 6),
                        indicatorbackground=FIELD, indicatorforeground=GOLD, focuscolor=GOLD,
                        upperbordercolor="#526273", lowerbordercolor="#526273")
        style.map("Shift.TCheckbutton",
                  background=[("disabled", PANEL), ("selected", "active", "#2b3c47"),
                              ("active", "#263645"), ("selected", "#22323d")],
                  foreground=[("disabled", "#738392"), ("selected", GOLD), ("active", TEXT)],
                  indicatorbackground=[("disabled", "#202b36"), ("selected", GOLD), ("active", "#253849")],
                  indicatorforeground=[("disabled", "#738392"), ("selected", BG)],
                  upperbordercolor=[("disabled", "#334354"), ("active", GOLD), ("selected", GOLD)],
                  lowerbordercolor=[("disabled", "#334354"), ("active", GOLD), ("selected", GOLD)])
        style.configure("TEntry", fieldbackground=FIELD, foreground=TEXT, insertcolor=TEXT, padding=7,
                        bordercolor="#405163", lightcolor=FIELD, darkcolor=FIELD)
        style.map("TEntry", fieldbackground=[("readonly", FIELD)], foreground=[("readonly", TEXT)],
                  bordercolor=[("focus", GOLD)], lightcolor=[("focus", FIELD)], darkcolor=[("focus", FIELD)])
        style.configure("TCombobox", fieldbackground=FIELD, foreground=TEXT, arrowcolor=GOLD, padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", FIELD)], foreground=[("readonly", TEXT)])
        style.configure("TNotebook", background=BG, borderwidth=0, bordercolor="#334354", lightcolor=BG, darkcolor=BG)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(12, 5))
        style.map("TNotebook.Tab", background=[("selected", FIELD)], foreground=[("selected", GOLD)])
        root.option_add("*TCombobox*Listbox.background", FIELD)
        root.option_add("*TCombobox*Listbox.foreground", TEXT)
        outer = ttk.Frame(root, style="Outer.TFrame", padding=20)
        outer.pack(fill="both", expand=True)
        title = ttk.Frame(outer, style="Outer.TFrame")
        title.pack(fill="x", pady=(0, 12))
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "Path_of_Exile_2_Logo.png"
        original_logo = tk.PhotoImage(master=root, file=str(logo_path), format="png")
        scale = max(1, (original_logo.height() + 75) // 76)
        self.logo = original_logo.subsample(scale, scale)
        tk.Label(title, image=self.logo, bg=BG, borderwidth=0).pack(side="left", padx=(0, 8))
        tk.Label(title, text="/", font=("Segoe UI Semibold", 24), fg=GOLD, bg=BG).pack(side="left", padx=(0, 8))
        reroller_path = logo_path.parent / "reroller.png"
        original_reroller = tk.PhotoImage(master=root, file=str(reroller_path), format="png")
        scale = max(1, (original_reroller.height() + 75) // 76)
        self.reroller_logo = original_reroller.subsample(scale * 2, scale * 2)
        tk.Label(title, image=self.reroller_logo, bg=BG, borderwidth=0).pack(side="left")
        language_frame = ttk.Frame(title, style="Outer.TFrame")
        language_frame.pack(side="right")
        language_row = ttk.Frame(language_frame, style="Outer.TFrame")
        language_row.pack(anchor="e")
        self.translated(tk.Label(language_row, fg=MUTED, bg=BG, font=("Segoe UI Semibold", 10)), "language_heading").pack(side="left", padx=(0, 12))
        self.language_combo = LanguageDropdown(language_row, self.change_language, self.language)
        self.language_combo.pack(side="left")
        tk.Label(language_frame, text=f"v{__version__}  •  Chaos Orb", fg=MUTED, bg=BG, font=("Segoe UI", 9)).pack(anchor="e", pady=(4, 0))

        calibration = self.translated(ttk.LabelFrame(outer, padding=12), "calibration_heading")
        calibration.pack(fill="x", pady=(0, 10))
        help_row = ttk.Frame(calibration)
        help_row.pack(fill="x")
        self.translated(ttk.Label(help_row), "calibration_help").pack(side="left")
        self.see_how_button = self.translated(tk.Button(help_row, command=self.show_calibration_image,
            font=("Segoe UI", 10, "underline"), fg=GOLD, bg=PANEL, activebackground=PANEL,
            activeforeground=TEXT, relief="flat", borderwidth=0, cursor="hand2", padx=4, pady=0), "see_how")
        self.see_how_button.pack(side="left", padx=(10, 0))
        row = ttk.Frame(calibration)
        row.pack(fill="x", pady=(10, 0))
        self.calibration_label = tk.StringVar()
        ttk.Label(row, textvariable=self.calibration_label, style="Muted.TLabel").pack(side="left")
        self.read_button = self.translated(ttk.Button(row, command=self.read_item), "read_button")
        self.read_button.pack(side="right")
        self.probe_button = self.translated(ttk.Button(row, command=self.probe_shift), "probe_button")
        self.probe_button.pack(side="right", padx=8)

        shortcuts = tk.Frame(calibration, bg=FIELD, highlightbackground="#334354", highlightthickness=1, padx=8, pady=7)
        shortcuts.pack(fill="x", pady=(10, 0))
        self.translated(tk.Label(shortcuts, bg=FIELD, fg=MUTED, font=("Segoe UI Semibold", 9)), "shortcuts_heading").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))
        bindings = [("F6", "shortcut_currency"), ("F7", "shortcut_item"), ("F8 / Shift+F8", "shortcut_stop"),
                    ("Ctrl+Alt+C", "shortcut_copy"), ("Esc", "shortcut_escape"), ("↑ ↓ / Enter", "shortcut_select"),
                    ("Tab / Shift+Tab", "shortcut_focus"), ("Space", "shortcut_activate"), ("Alt+F4", "shortcut_close")]
        for index, (keys, description) in enumerate(bindings):
            row_index, column = divmod(index, 3)
            shortcuts.columnconfigure(column, weight=1, uniform="shortcuts")
            cell = tk.Frame(shortcuts, bg=FIELD)
            cell.grid(row=row_index + 1, column=column, sticky="w", padx=(0, 8), pady=2)
            tk.Label(cell, text=keys, bg="#263645", fg=GOLD, font=("Consolas", 9, "bold"), padx=5, pady=2).pack(side="left", padx=(0, 6))
            self.translated(tk.Label(cell, bg=FIELD, fg=TEXT, font=("Segoe UI", 9), anchor="w"), description).pack(side="left")
        self.translated(tk.Label(shortcuts, bg=FIELD, fg=MUTED, font=("Segoe UI", 8)), "shortcut_context").grid(row=4, column=0, columnspan=3, sticky="w", pady=(5, 0))

        target = self.translated(ttk.LabelFrame(outer, padding=12), "target_heading")
        target.pack(fill="x", pady=(0, 10))
        selectors = ttk.Frame(target)
        selectors.pack(fill="x")
        selectors.columnconfigure(0, weight=1, uniform="selectors")
        selectors.columnconfigure(1, weight=1, uniform="selectors")
        self.translated(ttk.Label(selectors), "category_label").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.translated(ttk.Label(selectors), "modifier_label").grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 5))
        self.category_combo = SearchDropdown(selectors, self.select_category)
        self.category_combo.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.target_combo = SearchDropdown(selectors, self.select_modifier)
        self.target_combo.grid(row=1, column=1, sticky="ew", padx=(6, 0))
        budget_panel = ttk.Frame(selectors, padding=(0, 16, 12, 0))
        budget_panel.grid(row=2, column=0, sticky="new", padx=(0, 6))
        modifier_panel = ttk.Frame(selectors, padding=(0, 12, 0, 0))
        modifier_panel.grid(row=2, column=1, sticky="new", padx=(6, 0))

        self.description = tk.StringVar()
        description_label = ttk.Label(modifier_panel, textvariable=self.description, justify="left", foreground=GOLD, wraplength=420)
        description_label.pack(fill="x", pady=(0, 8))
        description_label.bind("<Configure>", lambda event: description_label.configure(wraplength=max(180, event.width)))
        self.custom_frame = ttk.Frame(modifier_panel)
        self.translated(ttk.Label(self.custom_frame), "custom_label").pack(anchor="w", pady=(0, 4))
        self.template = tk.StringVar(value=self.settings.get("template", "+# to Level of all Melee Skills"))
        if self.modifier_id:
            self.template.set(self.catalog.modifiers[self.modifier_id].template)
        self.custom_entry = ttk.Entry(self.custom_frame, textvariable=self.template)
        self.custom_entry.pack(fill="x")
        self.custom_entry.bind("<KeyRelease>", self._custom_changed)
        self.custom_frame.pack(fill="x", pady=(0, 8))
        self.values_frame = ttk.Frame(modifier_panel)
        self.values_frame.pack(fill="x", pady=(0, 8))
        self.metadata = tk.StringVar()
        metadata_label = ttk.Label(modifier_panel, textvariable=self.metadata, style="Muted.TLabel", wraplength=420, justify="left")
        metadata_label.pack(fill="x", pady=(0, 8))
        metadata_label.bind("<Configure>", lambda event: metadata_label.configure(wraplength=max(180, event.width)))
        self.details_button = self.translated(ttk.Button(modifier_panel, command=self.catalog_details), "catalog_details")
        self.details_button.pack(anchor="w")
        self.translated(ttk.Label(modifier_panel, style="Muted.TLabel", wraplength=420), "one_goal").pack(anchor="w", pady=(10, 0))

        budget_row = ttk.Frame(budget_panel)
        budget_row.pack(fill="x")
        self.translated(ttk.Label(budget_row, font=("Segoe UI Semibold", 10)), "budget_label").pack(side="left")
        self.budget = tk.StringVar(value="10" if self.demo else "")
        self.budget_entry = ttk.Entry(budget_row, textvariable=self.budget, width=9)
        self.budget_entry.pack(side="left", padx=(12, 0))
        self.budget_help = self.translated(ttk.Label(budget_panel, style="Muted.TLabel", justify="left", wraplength=400), "budget_help")
        self.budget_help.pack(fill="x", pady=(8, 12))
        self.budget_help.bind("<Configure>", lambda event: self.budget_help.configure(wraplength=max(180, event.width)))
        self.repeat_mode = tk.BooleanVar(value=False)
        self.repeat_check = self.translated(ttk.Checkbutton(budget_panel, variable=self.repeat_mode, style="Shift.TCheckbutton"), "repeat_label")
        self.repeat_check.pack(anchor="w")
        repeat_help = self.translated(ttk.Label(budget_panel, style="Muted.TLabel", justify="left", wraplength=400), "repeat_help")
        repeat_help.pack(fill="x", padx=(8, 0), pady=(3, 0))
        repeat_help.bind("<Configure>", lambda event: repeat_help.configure(wraplength=max(180, event.width)))
        self.eligibility = tk.StringVar()
        eligibility_label = ttk.Label(target, textvariable=self.eligibility, foreground="#efb08e", wraplength=885, justify="left")
        eligibility_label.pack(fill="x", pady=(12, 0))
        eligibility_label.bind("<Configure>", lambda event: eligibility_label.configure(wraplength=max(180, event.width)))

        actions = ttk.Frame(outer, style="Outer.TFrame")
        actions.pack(fill="x", pady=(0, 10))
        self.go_button = self.translated(ttk.Button(actions, style="Go.TButton", command=self.go, width=17), "go")
        self.go_button.pack(side="left")
        self.stop_button = self.translated(ttk.Button(actions, command=self.request_stop, width=17), "stop_button")
        self.stop_button.pack(side="left", padx=10)
        self.translated(ttk.Button(actions, command=self.guide), "guide").pack(side="right")
        stats = ttk.Frame(outer, style="Outer.TFrame")
        stats.pack(fill="x", pady=(0, 10))
        self.attempts, self.verified, self.rate = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for index, var in enumerate((self.attempts, self.verified, self.rate)):
            stats.columnconfigure(index, weight=1, uniform="stats")
            card = ttk.Frame(stats, padding=(10, 12))
            card.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 4, 0 if index == 2 else 4))
            ttk.Label(card, textvariable=var, anchor="center", font=("Segoe UI Semibold", 11)).pack(fill="x")
        self.status = tk.StringVar()
        tk.Label(outer, textvariable=self.status, bg=BG, fg=GREEN, anchor="w", justify="left", wraplength=910, font=("Segoe UI", 11)).pack(fill="x", pady=(0, 8))
        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill="both", expand=True)
        item_frame, log_frame = ttk.Frame(self.notebook, padding=8), ttk.Frame(self.notebook, padding=8)
        self.notebook.add(item_frame)
        self.notebook.add(log_frame)
        self.item_text, self.log_text = self._text_area(item_frame), self._text_area(log_frame)
        self.item_text.tag_configure("fractured", foreground=GOLD)
        self.item_text.tag_configure("heading", foreground=GREEN)
        self.footer = self.translated(tk.Label(outer, fg=MUTED, bg=BG, font=("Segoe UI", 9)), "footer")
        self.footer.pack(side="bottom", anchor="w", pady=(8, 0), before=self.notebook)

    def _text_area(self, parent):
        scroll = ttk.Scrollbar(parent)
        scroll.pack(side="right", fill="y")
        text = tk.Text(parent, wrap="word", height=5, bg=FIELD, fg=TEXT, font=("Consolas", 10), borderwidth=0,
                       padx=12, pady=10, state="disabled", yscrollcommand=scroll.set)
        text.pack(fill="both", expand=True)
        scroll.configure(command=text.yview)
        return text

    @staticmethod
    def _write(widget, text, tag=None, clear=False):
        widget.configure(state="normal")
        if clear:
            widget.delete("1.0", "end")
        widget.insert("end", text, tag or ())
        widget.configure(state="disabled")

    def set_status(self, message: Message):
        self.current_status = message
        self.status.set(message.text(self.language))

    def change_language(self, language):
        if self.running or language not in LANGUAGES:
            self.language_combo.select(self.language)
            return
        self.language = language
        self._apply_language()
        self.persist()

    def _apply_language(self):
        self.root.title("PoE 2 Reroller" + (" — " + self.tr("simulation_title") if self.demo else ""))
        self.language_combo.select(self.language)
        for widget, key in self.localized_widgets:
            widget.configure(text=self.tr(key))
        self.notebook.tab(0, text=self.tr("item_tab"))
        self.notebook.tab(1, text=self.tr("log_tab"))
        self.category_combo.prompt = self.target_combo.prompt = self.tr("search")
        entries = [(c.id, category_label(c.label, self.language)) for c in self.catalog.categories.values()]
        order = ["group_weapons", "group_armour", "group_accessories", "group_offhands", "group_jewels",
                 "group_flasks", "group_relics", "group_tablets", "group_waystones"]
        entries.sort(key=lambda entry: (order.index(self.catalog.categories[entry[0]].group_key), entry[1].casefold()))
        self.category_combo.set_entries(entries, self.category_id,
                                        groups={c.id: msg(c.group_key).text("en-US") for c in self.catalog.categories.values()})
        self._modifier_entries()
        self._rebuild_minimums()
        self._refresh_calibration()
        self._render_item()
        self._render_stats()
        self._render_log()
        self.status.set(self.current_status.text(self.language))
        self._update_description()
        self._update_go_state()

    def _modifier_entries(self):
        category = self.catalog.categories.get(self.category_id)
        entries = [("custom", self.tr("custom"))]
        groups = {}
        if category:
            for generation, heading in ((1, "Base Prefixes"), (2, "Base Suffixes")):
                for modifier in category.base_affixes:
                    if modifier.generation == generation:
                        entries.append((modifier.id, modifier.template.replace("\n", " / ")))
                        groups[modifier.id] = heading
        self.target_combo.set_entries(entries, self.modifier_id or "custom", groups=groups)

    def select_category(self, identifier):
        if self.running:
            return
        previous = self.catalog.modifiers.get(self.modifier_id)
        changed = identifier != self.category_id
        self.category_id = identifier
        if previous and changed:
            equivalent = next((m for m in self.catalog.categories[identifier].modifiers
                               if (m.template, m.source, m.families, m.generation) == (previous.template, previous.source, previous.families, previous.generation)), None)
            self.modifier_id = equivalent.id if equivalent else None
            if equivalent is None:
                self.template.set("")
                self._rebuild_minimums([])
                self.set_status(msg("catalog_selection_changed"))
        self._modifier_entries()
        self._update_description()
        self._update_go_state()
        self.persist()

    def select_modifier(self, identifier):
        if self.running:
            return
        previous = self.template.get()
        self.modifier_id = None if identifier == "custom" else identifier
        if self.modifier_id:
            modifier = self.catalog.modifiers[self.modifier_id]
            self.template.set(modifier.template)
            if previous != modifier.template:
                tiers = modifier.tiers
                eligible = modifier.available_tiers(self.item.level) if self.item else ()
                default = (eligible or tiers)[-1]["values"] if tiers else []
                self._rebuild_minimums([bounds[0] for bounds in default])
        self._update_description()
        self._update_go_state()
        self.persist()

    def _custom_changed(self, _=None):
        if len(self.minimums) != self.template.get().count("#"):
            self._rebuild_minimums()
        self._update_description()
        self._update_go_state()

    def _rebuild_minimums(self, values=None):
        previous = values if values is not None else [v.get() for v in self.minimums]
        for child in self.values_frame.winfo_children():
            child.destroy()
        self.minimums = []
        count = self.template.get().count("#")
        if count > 12:
            ttk.Label(self.values_frame, text=self.tr("too_many_values")).grid(row=0, column=0)
            return
        if count == 0:
            ttk.Label(self.values_frame, text=self.tr("text_target"), style="Muted.TLabel").grid(row=0, column=0)
        for i in range(count):
            row, col = divmod(i, 2)
            ttk.Label(self.values_frame, text=self.tr("minimum", index=i + 1)).grid(row=row, column=col * 2, padx=(0, 5), pady=3)
            var = tk.StringVar(value=previous[i] if i < len(previous) else "")
            ttk.Entry(self.values_frame, textvariable=var, width=9).grid(row=row, column=col * 2 + 1, padx=(0, 14), pady=3)
            var.trace_add("write", lambda *_: self._update_go_state())
            self.minimums.append(var)

    def _update_description(self):
        modifier = self.catalog.modifiers.get(self.modifier_id)
        self.details_button.configure(state="normal" if modifier and not self.running else "disabled")
        if modifier:
            self.custom_frame.pack_forget()
            self.description.set(modifier.template)
            levels = [t["level"] for t in modifier.tiers]
            kind = self.tr("prefix" if modifier.generation == 1 else "suffix" if modifier.generation == 2 else "special")
            source = self.tr("chaos_source") if modifier.chaos else self.catalog.source_label(modifier)
            text = self.tr("source_details", kind=kind, source=source, low=min(levels, default=0), high=max(levels, default=0), count=len(levels))
            if not modifier.chaos:
                text += " · " + self.tr("chaos_equivalent" if self.catalog.chaos_alternatives(modifier) else "modifier_not_chaos")
            self.metadata.set(text)
        else:
            if not self.custom_frame.winfo_manager():
                self.custom_frame.pack(fill="x", pady=(0, 5), before=self.values_frame)
            self.description.set(self.template.get())
            self.metadata.set(self.tr("custom_help"))

    def make_target(self):
        return Target.create(self.template.get(), [v.get() for v in self.minimums])

    def _validate_target(self, item, target, category_id, modifier_id):
        if target.matches(item):
            return
        if category_id is None:
            raise RerollError("category_required")
        self.catalog.validate(category_id, modifier_id, item, target)

    def _update_go_state(self):
        if not hasattr(self, "go_button"):
            return
        allowed = not self.running and self.catalog.complete and self.hotkeys.stop_available
        issue = None
        modifier = self.catalog.modifiers.get(self.modifier_id)
        if self.category_id is None:
            allowed = False
            issue = msg("category_required")
        elif modifier and not self.catalog.chaos_alternatives(modifier):
            allowed = False
            issue = msg("modifier_not_chaos")
        if self.item:
            try:
                target = self.make_target()
                self._validate_target(self.item, target, self.category_id, self.modifier_id)
                if target.matches(self.item):
                    allowed = not self.running and self.hotkeys.stop_available
                    issue = None
            except RerollError as exc:
                allowed = False
                issue = exc.message
        else:
            try:
                self.make_target()
            except RerollError as exc:
                allowed = False
                issue = exc.message
        if not self.catalog.complete:
            issue = msg("catalog_incomplete")
        self.eligibility.set(issue.text(self.language) if issue else "")
        self.go_button.configure(state="normal" if allowed else "disabled")

    def _refresh_calibration(self):
        if self.demo:
            label = self.tr("calibration_demo")
        else:
            calibration = self.calibration
            currency = str(calibration.currency) if calibration and calibration.currency else self.tr("missing")
            item = str(calibration.item) if calibration and calibration.item else self.tr("missing")
            label = self.tr("calibration_points", currency=currency, item=item)
        self.calibration_label.set(label)

    def capture(self, kind):
        if self.running or self.demo:
            return
        try:
            bounds, point = capture_point()
            current = self.calibration if self.calibration and self.calibration.bounds == bounds else Calibration(bounds)
            candidate = replace(current, **{kind: point})
            candidate.validate()
            self.calibration = candidate
            self._refresh_calibration()
            self.persist()
            self.set_status(msg("calibration_saved"))
        except RerollError as exc:
            self.set_status(exc.message)

    def persist(self):
        if not self.demo:
            try:
                save_settings(self.calibration, self.template.get(), [v.get() for v in self.minimums], language=self.language,
                              category_id=self.category_id, modifier_id=self.modifier_id)
            except OSError as exc:
                self.log.warning("settings_save_failed %s", exc)

    def _set_running(self, running):
        self.running = running
        self._update_description()
        for widget in (self.read_button, self.probe_button, self.see_how_button, self.repeat_check, self.budget_entry, self.custom_entry):
            widget.configure(state="disabled" if running else "normal")
        self.language_combo.set_disabled(running)
        self.category_combo.set_disabled(running)
        self.target_combo.set_disabled(running)
        for child in self.values_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                child.configure(state="disabled" if running else "normal")
        if not running and self.item:
            inferred = self.catalog.infer(self.item)
            if inferred and inferred != self.category_id:
                self.select_category(inferred)
        self._update_go_state()

    def _connection(self):
        if self.demo:
            return DemoConnection(self.stop)
        if not self.calibration or not self.calibration.item:
            raise RerollError("item_calibration_required")
        return WindowsConnection(self.calibration, self.stop)

    def _start(self, task):
        if self.running:
            return
        self.stop.clear()
        self._set_running(True)
        self.set_status(msg("simulation_start" if self.demo else "activating"))
        def work():
            connection = None
            try:
                connection = self._connection()
                task(connection)
            except Exception as exc:
                self.log.exception("run_stopped")
                self.events.put(("error", exc.message if isinstance(exc, RerollError) else msg("unexpected_error", detail=str(exc))))
            finally:
                if connection:
                    try:
                        connection.close()
                    except Exception:
                        self.log.exception("cleanup_failed")
                        self.events.put(("error", msg("cleanup_failed")))
                    if getattr(connection, "selection_pending", False):
                        self.events.put(("status", msg("cursor_pending")))
                self.events.put(("done", None))
        self.worker = threading.Thread(target=work, name="reroller-worker", daemon=False)
        self.worker.start()

    def read_item(self):
        def task(connection):
            item = connection.read_item()
            validate_item(item)
            self.events.put(("item", item))
            self.events.put(("status", msg("read_ok")))
        self._start(task)

    def probe_shift(self):
        if self.demo:
            self.set_status(msg("probe_demo"))
            return
        if not self.calibration or not self.calibration.item or not self.calibration.currency:
            self.set_status(msg("calibrate_both"))
            return
        def task(connection):
            before = connection.read_item()
            validate_item(before)
            connection.read_currency()
            connection.begin_repeat()
            for _ in range(3):
                after = connection.read_item()
                if after.fingerprint != before.fingerprint:
                    raise RerollError("probe_changed")
            self.events.put(("item", after))
            self.events.put(("status", msg("probe_ok")))
        self._start(task)

    def go(self):
        if self.running:
            return
        try:
            if not self.hotkeys.stop_available:
                raise RerollError("f8_required")
            if not self.demo and (not self.calibration or not self.calibration.currency or not self.calibration.item):
                raise RerollError("calibrate_both")
            target = self.make_target()
            try:
                budget = int(self.budget.get())
                if budget <= 0:
                    raise ValueError
            except ValueError:
                raise RerollError("budget_invalid")
            category_id, modifier_id = self.category_id, self.modifier_id
            if self.item:
                self._validate_target(self.item, target, category_id, modifier_id)
            repeat = self.repeat_mode.get() and budget > 1
            if repeat and not self.hotkeys.repeat_stop_available:
                raise RerollError("shift_f8_busy")
            if repeat and self.demo:
                raise RerollError("shift_demo")
        except RerollError as exc:
            self.set_status(exc.message)
            return
        self.persist()
        self.last_result = None
        def task(connection):
            engine = Engine(connection, target, budget, self.stop,
                            emit=lambda progress: self.events.put(("progress", progress)), repeat=repeat,
                            validate_target=lambda item: self._validate_target(item, target, category_id, modifier_id))
            self.events.put(("result", engine.run()))
        self._start(task)

    def request_stop(self):
        self.stop.set()
        if self.running:
            self.set_status(msg("stopping"))

    def show_item(self, item):
        self.item = item
        inferred = self.catalog.infer(item)
        candidates = self.catalog.candidates(item)
        if inferred and inferred != self.category_id:
            self.select_category(inferred)
        elif self.category_id not in {c.id for c in candidates}:
            self.category_id = None
            if self.modifier_id:
                self.modifier_id = None
                self.template.set("")
                self._rebuild_minimums([])
            self._modifier_entries()
            self.category_combo.select(None)
        self.category_combo.select(self.category_id)
        self._render_item()
        self._update_description()
        self._update_go_state()

    def _render_item(self):
        if not self.item:
            self._write(self.item_text, self.tr("item_empty"), clear=True)
            return
        item = self.item
        self._write(self.item_text, f"{item.name}\n{item.base}\n" + self.tr("item_summary", rarity=item.rarity, level=item.level) + "\n\n", "heading", clear=True)
        for modifier in item.modifiers:
            label = self.tr("fractured_label") if modifier.fractured else ""
            if modifier.kind != "explicit":
                label += "[" + self.tr("implicit" if modifier.kind == "implicit" else "other") + "] "
            self._write(self.item_text, label + modifier.text + "\n\n", "fractured" if modifier.fractured else None)

    def _render_stats(self):
        progress = self.last_progress
        self.attempts.set(self.tr("attempts", count=progress.attempts if progress else 0))
        self.verified.set(self.tr("verified", count=progress.verified if progress else 0))
        self.rate.set(self.tr("rate", rate=f"{progress.attempts / progress.elapsed:.2f}") if progress and progress.elapsed > 0 else self.tr("no_rate"))

    def _append_log(self, message):
        self.log_messages.append(message)
        self.log_messages = self.log_messages[-500:]
        self.log.info("%s %s", message.key, json.dumps(asdict(message), ensure_ascii=False))
        self._write(self.log_text, message.text(self.language) + "\n")
        self.log_text.see("end")

    def _render_log(self):
        self._write(self.log_text, "\n".join(m.text(self.language) for m in self.log_messages) + "\n", clear=True)

    def _pump(self):
        for name in self.hotkeys.poll():
            self.request_stop() if name == "stop" else self.capture(name)
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "item":
                    self.show_item(payload)
                elif kind in {"status", "error"}:
                    self.set_status(payload)
                    self._append_log(payload)
                elif kind == "progress":
                    self.last_progress = payload
                    message = payload.message or msg("detail", detail=payload.status)
                    self.set_status(message)
                    self._render_stats()
                    if payload.item:
                        self.show_item(payload.item)
                    self._append_log(message)
                elif kind == "result":
                    self.last_result = payload
                    self.set_status(payload.message or msg("detail", detail=payload.reason))
                    self.log.info("result %s", json.dumps(asdict(payload), ensure_ascii=False))
                    if payload.matched:
                        winsound.MessageBeep(winsound.MB_OK)
                elif kind == "done":
                    self._set_running(False)
        except queue.Empty:
            pass
        if self.closing and not self.running:
            self.language_combo.close_popup()
            self.category_combo.close_popup()
            self.target_combo.close_popup()
            self.hotkeys.close()
            self.root.destroy()
            return
        self.root.after(25, self._pump)

    def guide(self):
        messagebox.showinfo(self.tr("guide"), self.tr("guide_body", path=data_directory()), parent=self.root)

    def show_calibration_image(self):
        if self.running:
            return
        if self.calibration_popup and self.calibration_popup.winfo_exists():
            self.calibration_popup.lift()
            return
        dialog = self.calibration_popup = tk.Toplevel(self.root)
        dialog.title(self.tr("calibration_image_title"))
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        image_path = Path(__file__).resolve().parent.parent / "assets" / "info.png"
        dialog.image = tk.PhotoImage(master=dialog, file=str(image_path), format="png")
        width = min(dialog.image.width() + 40, self.root.winfo_screenwidth() - 100)
        height = min(dialog.image.height() + 100, self.root.winfo_screenheight() - 100)
        dialog.geometry(f"{width}x{height}+{(self.root.winfo_screenwidth() - width) // 2}+{max(20, (self.root.winfo_screenheight() - height) // 2)}")
        dialog.minsize(400, 360)

        def close_image(_=None):
            dialog.grab_release()
            dialog.destroy()
            self.calibration_popup = None

        toolbar = tk.Frame(dialog, bg=PANEL, padx=12, pady=8)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text=self.tr("calibration_image_title"), bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 12)).pack(side="left")
        close_button = tk.Button(toolbar, text=self.tr("close_image"), command=close_image,
            font=("Segoe UI Semibold", 12), bg="#993d3d", fg="white", activebackground="#bb4d4d",
            activeforeground="white", relief="flat", padx=16, pady=6, cursor="hand2")
        close_button.pack(side="right")
        frame = ttk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
        vertical = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set,
                         scrollregion=(0, 0, dialog.image.width(), dialog.image.height()))
        canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        canvas.create_image(0, 0, anchor="nw", image=dialog.image)
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(-int(event.delta / 120), "units"))
        dialog.bind("<Escape>", close_image)
        dialog.protocol("WM_DELETE_WINDOW", close_image)
        dialog.update_idletasks()
        dialog.grab_set()
        close_button.focus_set()

    def catalog_details(self):
        modifier = self.catalog.modifiers.get(self.modifier_id)
        if not modifier or self.running:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(self.tr("catalog_details"))
        dialog.geometry("800x550")
        dialog.transient(self.root)
        text = self._text_area(dialog)
        lines = [modifier.template, "", self.metadata.get(),
                 self.tr("family_details", families=", ".join(modifier.families)), ""]
        for tier in modifier.tiers:
            lines.extend([tier["name"], self.tr("tier_details", level=tier["level"], weight=tier["weight"],
                         values=" / ".join(f"{low} … {high}" for low, high in tier["values"]) or "—"),
                         str(tier["code"] or ""), ""])
        self._write(text, "\n".join(lines))
        dialog.bind("<Escape>", lambda _: dialog.destroy())
        dialog.wait_visibility()
        dialog.grab_set()
        dialog.focus_set()

    def close(self):
        self.closing = True
        self.stop.set()
        self.persist()
        self.set_status(msg("closing"))
