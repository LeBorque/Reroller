# Python 3.14 | reroller/widgets.py | searchable catalog dropdown
from __future__ import annotations

from pathlib import Path

import tkinter as tk
from tkinter import ttk
from tkinter.font import Font

from .catalog import search_entries


class LanguageDropdown(tk.Frame):
    LABELS = {"sv-SE": "SE", "en-US": "US"}

    def __init__(self, parent, command, language):
        super().__init__(parent, bg="#40596e", padx=1, pady=1)
        self.command = command
        self.disabled = False
        self.popup = None
        self.flags = self._flags()
        self.button = tk.Button(self, compound="left", font=("Segoe UI Semibold", 10),
            bg="#111c27", fg="#edf0f2", activebackground="#263645", activeforeground="#e8bd72",
            disabledforeground="#738392", relief="flat", borderwidth=0, padx=12, pady=7,
            cursor="hand2", highlightthickness=0, command=self.open)
        self.button.pack(fill="both", expand=True)
        self.button.bind("<Return>", lambda _: self.open())
        self.button.bind("<Down>", lambda _: self.open())
        self.button.bind("<Enter>", lambda _: self.configure(bg="#e8bd72") if not self.disabled else None)
        self.button.bind("<Leave>", lambda _: self.configure(bg="#40596e"))
        self.button.bind("<FocusIn>", lambda _: self.configure(bg="#e8bd72") if not self.disabled else None)
        self.button.bind("<FocusOut>", lambda _: self.configure(bg="#40596e"))
        self.select(language)

    def _flags(self):
        assets = Path(__file__).resolve().parent.parent / "assets"
        return {
            language: tk.PhotoImage(master=self, file=str(assets / filename), format="png")
            for language, filename in (("sv-SE", "flag_se.png"), ("en-US", "flag_us.png"))
        }

    def select(self, language):
        self.selected_id = language
        self.button.configure(image=self.flags[language], text=f"  {self.LABELS[language]}    ▾")

    def set_disabled(self, disabled):
        self.disabled = disabled
        self.close_popup()
        self.button.configure(state="disabled" if disabled else "normal", cursor="arrow" if disabled else "hand2")

    def choose(self, language):
        if self.disabled:
            return
        self.close_popup()
        self.command(language)
        self.button.focus_set()

    def open(self):
        if self.disabled:
            return
        if self.popup:
            self.close_popup()
            return
        popup = self.popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#40596e", padx=1, pady=1)
        choices = []
        for language, label in self.LABELS.items():
            selected = language == self.selected_id
            button = tk.Button(popup, image=self.flags[language], text=f"  {label}", compound="left", anchor="w",
                font=("Segoe UI Semibold", 10), bg="#263645" if selected else "#111c27",
                fg="#e8bd72" if selected else "#edf0f2", activebackground="#304254", activeforeground="#e8bd72",
                relief="flat", borderwidth=0, highlightthickness=1, highlightcolor="#e8bd72",
                highlightbackground="#263645" if selected else "#111c27", padx=12, pady=9,
                cursor="hand2", command=lambda code=language: self.choose(code))
            button.pack(fill="x", padx=4, pady=3)
            button.bind("<Return>", lambda _, code=language: self.choose(code))
            choices.append(button)
        def navigate(event):
            current = choices.index(popup.focus_get()) if popup.focus_get() in choices else 0
            choices[(current + (1 if event.keysym == "Down" else -1)) % len(choices)].focus_set()
            return "break"
        popup.bind("<Up>", navigate)
        popup.bind("<Down>", navigate)
        popup.bind("<Escape>", lambda _: self.close_popup())
        def outside(event):
            if not (popup.winfo_rootx() <= event.x_root < popup.winfo_rootx() + popup.winfo_width()
                    and popup.winfo_rooty() <= event.y_root < popup.winfo_rooty() + popup.winfo_height()):
                self.close_popup()
        popup.bind("<Button-1>", outside)
        popup.update_idletasks()
        popup.geometry(f"{max(150, self.winfo_width())}x{popup.winfo_reqheight()}+{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height() + 5}")
        popup.update_idletasks()
        popup.lift()
        popup.grab_set()
        choices[list(self.LABELS).index(self.selected_id)].focus_force()

    def close_popup(self):
        if self.popup:
            popup, self.popup = self.popup, None
            try:
                popup.grab_release()
                popup.destroy()
            except tk.TclError:
                pass


class SearchDropdown(ttk.Frame):
    def __init__(self, parent, command, *, background="#111c27", foreground="#edf0f2"):
        super().__init__(parent)
        self.command = command
        self.background, self.foreground = background, foreground
        self.entries: list[tuple[str, str]] = []
        self.groups: dict[str, str] = {}
        self.selected_id: str | None = None
        self.disabled = False
        self.popup = None
        self.prompt = "Search…"
        self.display = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.display, state="readonly")
        self.entry.pack(side="left", fill="x", expand=True)
        self.arrow = ttk.Button(self, text="▾", width=2, command=self.open)
        self.arrow.pack(side="right")
        self.entry.bind("<Button-1>", lambda _: self.open())
        self.entry.bind("<Down>", lambda _: self.open())
        self.entry.bind("<Return>", lambda _: self.open())

    def set_entries(self, entries: list[tuple[str, str]], selected: str | None, *, groups: dict[str, str] | None = None):
        self.close_popup()
        self.entries = entries
        self.groups = groups or {}
        self.select(selected)

    def select(self, identifier: str | None):
        labels = dict(self.entries)
        self.selected_id = identifier if identifier in labels else None
        self.display.set(labels.get(self.selected_id, ""))

    def set_disabled(self, disabled: bool):
        self.disabled = disabled
        self.close_popup()
        self.entry.configure(state="disabled" if disabled else "readonly")
        self.arrow.configure(state="disabled" if disabled else "normal")

    def open(self):
        if self.disabled or self.popup:
            return
        popup = self.popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=self.background, borderwidth=1, relief="solid")
        width = max(260, self.winfo_width())
        x, y = self.winfo_rootx(), self.winfo_rooty() + self.winfo_height()
        height = min(330, max(160, popup.winfo_screenheight() - y - 50))
        popup.geometry(f"{width}x{height}+{x}+{y}")
        ttk.Label(popup, text=self.prompt).pack(fill="x", padx=7, pady=(5, 0))
        query = tk.StringVar()
        search = ttk.Entry(popup, textvariable=query)
        search.pack(fill="x", padx=7, pady=5)
        frame = ttk.Frame(popup)
        frame.pack(fill="both", expand=True)
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")
        horizontal = ttk.Scrollbar(popup, orient="horizontal")
        horizontal.pack(side="bottom", fill="x")
        style = ttk.Style(self)
        style.configure("Catalog.Treeview", background=self.background, fieldbackground=self.background,
                        foreground=self.foreground, font=("Segoe UI", 10), rowheight=25, borderwidth=0)
        style.map("Catalog.Treeview", background=[("selected", "#40596e")])
        listing = ttk.Treeview(frame, show="tree", selectmode="browse", style="Catalog.Treeview",
                              yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        listing.tag_configure("heading", font=("Segoe UI", 10, "bold"), foreground="#e8bd72")
        listing.pack(fill="both", expand=True)
        scroll.configure(command=listing.yview)
        horizontal.configure(command=listing.xview)
        selectable = {}
        font = Font(self, family="Segoe UI", size=10)

        def refresh(*_):
            visible = search_entries(self.entries, query.get())
            listing.delete(*listing.get_children())
            selectable.clear()
            grouped = {}
            for identifier, label in visible:
                grouped.setdefault(self.groups.get(identifier, ""), []).append((identifier, label))
            for group, entries in grouped.items():
                if group:
                    listing.insert("", "end", text=group, tags=("heading",))
                for identifier, label in entries:
                    row = listing.insert("", "end", text="    " + label)
                    selectable[row] = identifier
            listing.column("#0", width=max(width - 20, max((font.measure(label) + 50 for _, label in visible), default=0)), stretch=False)
            if selectable:
                first = next(iter(selectable))
                listing.selection_set(first)
                listing.focus(first)

        def choose(_=None):
            selected = listing.selection()
            if selected and selected[0] in selectable:
                identifier = selectable[selected[0]]
                self.select(identifier)
                self.close_popup()
                self.command(identifier)
            return "break"

        def down(_):
            listing.focus_set()
            return "break"

        def navigate(event):
            rows = list(selectable)
            if rows:
                selected = listing.selection()
                current = rows.index(selected[0]) if selected and selected[0] in rows else -1
                index = max(0, min(len(rows) - 1, current + (1 if event.keysym == "Down" else -1)))
                listing.selection_set(rows[index])
                listing.focus(rows[index])
                listing.see(rows[index])
            return "break"

        def click(event):
            row = listing.identify_row(event.y)
            if row in selectable:
                listing.selection_set(row)
                return choose()
            listing.selection_remove(*listing.selection())
            return "break"

        query.trace_add("write", refresh)
        listing.bind("<Return>", choose)
        listing.bind("<Up>", navigate)
        listing.bind("<Down>", navigate)
        listing.bind("<ButtonRelease-1>", click)
        search.bind("<Return>", choose)
        search.bind("<Down>", down)
        popup.bind("<Escape>", lambda _: self.close_popup())

        def outside(event):
            if not (popup.winfo_rootx() <= event.x_root < popup.winfo_rootx() + popup.winfo_width()
                    and popup.winfo_rooty() <= event.y_root < popup.winfo_rooty() + popup.winfo_height()):
                self.close_popup()
        popup.bind("<Button-1>", outside)
        refresh()
        popup.update_idletasks()
        popup.lift()
        popup.grab_set()
        search.focus_set()

    def close_popup(self):
        if self.popup:
            popup, self.popup = self.popup, None
            try:
                popup.grab_release()
                popup.destroy()
            except tk.TclError:
                pass
