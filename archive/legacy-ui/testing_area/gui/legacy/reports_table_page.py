"""
gui/reports_table_page.py

A filterable, sortable, paginated attendance report — recreates the
BFEAS web "Reports" screen (From/To date filter, Show-N-entries,
Search box, sortable columns, pagination footer) inside CustomTkinter.

Drop this file into your gui/ folder alongside attendance_page.py.

Data model note:
Your schema logs one row per scan (fingerprint_id, date, time, status),
not a paired check-in/check-out row like the web app implies. So this
page groups scans by (student, date) and treats the earliest scan of
the day as Time-In and the latest as Time-Out — that's the closest
faithful match to what the web screenshot is actually showing.

Wiring it in (once you're ready):
    from gui.reports_table_page import ReportsPage
    self.reports_page = ReportsPage(self)
    # inside whatever tab/frame you want it in:
    self.reports_page.build(some_tab_frame)

Requires one new function in core/database.py — see
database_addition_snippet.py in this same delivery.
"""

import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from gui.theme import get_theme_colors
from core.database import get_daily_attendance_summary, get_all_students, log_attendance

COLOR_MUTED = "#8b8b8b"
COLOR_ACCENT = "#3b82f6"

# (column_id, header_label, width, anchor)
COLUMNS = [
    ("no", "No.", 45, "center"),
    ("name", "Name", 170, "w"),
    ("student_no", "Student No.", 100, "center"),
    ("grade", "Grade", 60, "center"),
    ("section", "Section", 90, "center"),
    ("date", "Date", 95, "center"),
    ("day", "Day", 90, "center"),
    ("time_in", "Time-In", 85, "center"),
    ("time_out", "Time-Out", 85, "center"),
    ("status", "Status", 90, "center"),
]

# Maps the id shown in the treeview back to the underlying dict key used for sorting
SORT_KEYS = {
    "no": None,  # not sortable, it's just row position
    "name": "student_name",
    "student_no": "student_no",
    "grade": "grade",
    "section": "section",
    "date": "date",
    "day": "date",  # day derives from date, so sort by date underneath
    "time_in": "time_in",
    "time_out": "time_out",
    "status": "status",
}


def _day_name(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
    except Exception:
        return "N/A"


class ReportsPage:
    def __init__(self, app):
        self.app = app
        self.raw_rows = []      # rows for the current date range, straight from DB
        self.filtered_rows = [] # after search filter + sort applied
        self.page_size = 10
        self.current_page = 1
        self.sort_column = "date"
        self.sort_reverse = True

        self.tree = None
        self.from_entry = None
        self.to_entry = None
        self.search_var = None
        self.entries_var = None
        self.page_info_label = None
        self.prev_btn = None
        self.next_btn = None

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(self, parent):
        colors = get_theme_colors(ctk.get_appearance_mode())

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        # ---- Header ----
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Reports", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Home  ›  Reports", text_color=COLOR_MUTED,
                     font=("Segoe UI", 11)).grid(row=0, column=1, sticky="e")

        # ---- Filter bar: + / From / To / View Reports ----
        filter_card = ctk.CTkFrame(parent, corner_radius=10, fg_color=colors["card_background"])
        filter_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkButton(filter_card, text="+", width=36, command=self.open_add_dialog).grid(
            row=0, column=0, padx=(12, 20), pady=12, sticky="w"
        )
        ctk.CTkLabel(filter_card, text="From:").grid(row=0, column=1, padx=(0, 6), pady=12)
        self.from_entry = ctk.CTkEntry(filter_card, width=120, placeholder_text="yyyy-mm-dd")
        self.from_entry.grid(row=0, column=2, padx=(0, 16), pady=12)

        ctk.CTkLabel(filter_card, text="To:").grid(row=0, column=3, padx=(0, 6), pady=12)
        self.to_entry = ctk.CTkEntry(filter_card, width=120, placeholder_text="yyyy-mm-dd")
        self.to_entry.grid(row=0, column=4, padx=(0, 16), pady=12)

        ctk.CTkButton(filter_card, text="View Reports", width=120,
                      command=self.apply_date_filter).grid(row=0, column=5, padx=(0, 12), pady=12)

        # ---- Controls: Show N entries + Search ----
        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        controls.grid_columnconfigure(1, weight=1)

        show_frame = ctk.CTkFrame(controls, fg_color="transparent")
        show_frame.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(show_frame, text="Show").pack(side="left", padx=(0, 6))
        self.entries_var = ctk.StringVar(value="10")
        ctk.CTkOptionMenu(show_frame, values=["10", "25", "50", "100"], variable=self.entries_var,
                          width=70, command=self.on_entries_changed).pack(side="left")
        ctk.CTkLabel(show_frame, text="entries").pack(side="left", padx=(6, 0))

        search_frame = ctk.CTkFrame(controls, fg_color="transparent")
        search_frame.grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=(0, 6))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.on_search_changed)
        ctk.CTkEntry(search_frame, textvariable=self.search_var, width=200).pack(side="left")

        # ---- Table ----
        table_card = ctk.CTkFrame(parent, corner_radius=10, fg_color=colors["card_background"])
        table_card.grid(row=3, column=0, sticky="nsew")
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(0, weight=1)

        self._style_treeview(colors)

        tree_container = ctk.CTkFrame(table_card, fg_color="transparent")
        tree_container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        col_ids = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(tree_container, columns=col_ids, show="headings",
                                  style="Reports.Treeview", selectmode="browse")
        for col_id, label, width, anchor in COLUMNS:
            self.tree.heading(col_id, text=label, command=lambda c=col_id: self.sort_by(c))
            self.tree.column(col_id, width=width, anchor=anchor, stretch=(col_id == "name"))
        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

        # ---- Footer: "Showing X to Y of Z entries" + pagination ----
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        footer.grid_columnconfigure(0, weight=1)

        self.page_info_label = ctk.CTkLabel(footer, text="Showing 0 to 0 of 0 entries", text_color=COLOR_MUTED)
        self.page_info_label.grid(row=0, column=0, sticky="w")

        nav = ctk.CTkFrame(footer, fg_color="transparent")
        nav.grid(row=0, column=1, sticky="e")
        self.prev_btn = ctk.CTkButton(nav, text="Previous", width=90, command=lambda: self.change_page(-1))
        self.prev_btn.pack(side="left", padx=(0, 6))
        self.next_btn = ctk.CTkButton(nav, text="Next", width=90, command=lambda: self.change_page(1))
        self.next_btn.pack(side="left")

        # Default range: last 30 days, then load
        today = datetime.now().strftime("%Y-%m-%d")
        self.to_entry.insert(0, today)
        self.from_entry.insert(0, today)
        self.apply_date_filter()

        return table_card

    def _style_treeview(self, colors):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        dark = ctk.get_appearance_mode().lower() == "dark"
        bg = colors["card_background"]
        fg = "#e5e7eb" if dark else "#1f2937"
        heading_bg = colors["surface_background"]
        select_bg = COLOR_ACCENT

        style.configure("Reports.Treeview", background=bg, fieldbackground=bg, foreground=fg,
                        rowheight=28, borderwidth=0, font=("Segoe UI", 11))
        style.configure("Reports.Treeview.Heading", background=heading_bg, foreground=fg,
                        font=("Segoe UI", 11, "bold"), relief="flat")
        style.map("Reports.Treeview", background=[("selected", select_bg)],
                  foreground=[("selected", "#ffffff")])
        style.map("Reports.Treeview.Heading", background=[("active", heading_bg)])

    # ------------------------------------------------------------------
    # Data loading / filtering / sorting / pagination
    # ------------------------------------------------------------------
    def apply_date_filter(self):
        start = self.from_entry.get().strip()
        end = self.to_entry.get().strip()
        for value, label in ((start, "From"), (end, "To")):
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid Date", f"{label} date must be in yyyy-mm-dd format.", parent=self.app)
                return

        try:
            self.raw_rows = get_daily_attendance_summary(start, end)
        except Exception as exc:
            messagebox.showerror("Report Error", f"Could not load report: {exc}", parent=self.app)
            self.raw_rows = []

        self.current_page = 1
        self._recompute_and_render()

    def on_entries_changed(self, value):
        self.page_size = int(value)
        self.current_page = 1
        self._recompute_and_render()

    def on_search_changed(self, *args):
        self.current_page = 1
        self._recompute_and_render()

    def sort_by(self, col_id):
        key = SORT_KEYS.get(col_id)
        if key is None:
            return
        if self.sort_column == col_id:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col_id
            self.sort_reverse = False
        self._recompute_and_render()

    def change_page(self, delta):
        total_pages = max(1, -(-len(self.filtered_rows) // self.page_size))
        new_page = self.current_page + delta
        if 1 <= new_page <= total_pages:
            self.current_page = new_page
            self._render_page()

    def _recompute_and_render(self):
        query = (self.search_var.get() or "").strip().lower() if self.search_var else ""
        if query:
            def matches(row):
                haystack = " ".join(str(row.get(k, "")) for k in
                                     ("student_name", "student_no", "grade", "section", "status", "date"))
                return query in haystack.lower()
            rows = [r for r in self.raw_rows if matches(r)]
        else:
            rows = list(self.raw_rows)

        sort_key = SORT_KEYS.get(self.sort_column, "date")
        rows.sort(key=lambda r: (r.get(sort_key) or ""), reverse=self.sort_reverse)

        self.filtered_rows = rows
        self._render_page()

    def _render_page(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total = len(self.filtered_rows)
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total)
        page_rows = self.filtered_rows[start_idx:end_idx]

        for i, row in enumerate(page_rows, start=start_idx + 1):
            scan_count = row.get("scan_count", 1)
            status = "Present" if scan_count and scan_count >= 1 else "Absent"
            time_out = row.get("time_out") if scan_count and scan_count > 1 else "—"
            self.tree.insert("", "end", values=(
                i,
                row.get("student_name", "N/A"),
                row.get("student_no", "N/A"),
                row.get("grade", "N/A"),
                row.get("section", "N/A"),
                row.get("date", "N/A"),
                _day_name(row.get("date", "")),
                row.get("time_in", "N/A"),
                time_out,
                status,
            ))

        if total == 0:
            self.page_info_label.configure(text="Showing 0 to 0 of 0 entries")
        else:
            self.page_info_label.configure(
                text=f"Showing {start_idx + 1} to {end_idx} of {total} entries"
            )

        total_pages = max(1, -(-total // self.page_size))
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")

    # ------------------------------------------------------------------
    # "+" Add manual attendance record
    # ------------------------------------------------------------------
    def open_add_dialog(self):
        students = get_all_students()
        if not students:
            messagebox.showwarning("No Students", "Register a student before adding a manual record.", parent=self.app)
            return

        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Add Manual Attendance Record")
        dialog.geometry("380x320")
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Add Manual Attendance", font=("Segoe UI", 14, "bold")).pack(pady=(16, 12))

        student_labels = [f"{s['student_name']} ({s['student_no']})" for s in students]
        student_var = ctk.StringVar(value=student_labels[0])
        ctk.CTkLabel(dialog, text="Student:").pack(anchor="w", padx=24)
        ctk.CTkOptionMenu(dialog, values=student_labels, variable=student_var, width=320).pack(padx=24, pady=(0, 10))

        ctk.CTkLabel(dialog, text="Date (yyyy-mm-dd):").pack(anchor="w", padx=24)
        date_entry = ctk.CTkEntry(dialog, width=320)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.pack(padx=24, pady=(0, 10))

        ctk.CTkLabel(dialog, text="Time (HH:MM:SS):").pack(anchor="w", padx=24)
        time_entry = ctk.CTkEntry(dialog, width=320)
        time_entry.insert(0, datetime.now().strftime("%H:%M:%S"))
        time_entry.pack(padx=24, pady=(0, 16))

        def save():
            idx = student_labels.index(student_var.get())
            fingerprint_id = students[idx]["fingerprint_id"]
            date_str = date_entry.get().strip()
            time_str = time_entry.get().strip()
            try:
                when = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                messagebox.showerror("Invalid Input", "Check date/time format.", parent=dialog)
                return

            try:
                log_attendance(fingerprint_id, 999, "Present (Manual)", when)
            except Exception as exc:
                messagebox.showerror("Error", f"Could not save record: {exc}", parent=dialog)
                return

            dialog.destroy()
            self.apply_date_filter()

        ctk.CTkButton(dialog, text="Save Record", command=save).pack(pady=(0, 16))


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Reports Test GUI")
    root.geometry("1280x760")
    root.minsize(1100, 700)

    container = ctk.CTkFrame(root, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=18, pady=18)

    page = ReportsPage(app=root)
    page.build(container)

    root.mainloop()
