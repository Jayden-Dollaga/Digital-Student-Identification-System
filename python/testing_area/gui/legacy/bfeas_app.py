"""
BFEAS - Biometric Fingerprint Employee Attendance System
A CustomTkinter recreation of the web-based Reports/Attendance screen.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ---- Palette (matched to the source screenshot) ----
HEADER_BLUE = "#3f7fbf"
SIDEBAR_BLUE = "#123a5e"
SIDEBAR_BLUE_LIGHT = "#1c4a72"
SIDEBAR_SECTION = "#0c2c47"
ACCENT_BLUE = "#2f7bc4"
BODY_BG = "#eef1f5"
CARD_BG = "#ffffff"
TEXT_DARK = "#2b2b2b"
BORDER = "#dfe3e8"

SAMPLE_ROWS = [
    (1, "Gabriel Mefoni David", "mEQX64", "Manager",         "2022-04-11", "Monday",   "14:49", "15:12", "Present"),
    (2, "Patience Ntishor",     "7xNpYG", "Finance Officer",  "2022-04-11", "Monday",   "16:35", "16:41", "Present"),
    (3, "Inok Ifang-Ishor",     "JTxwB2", "Operation Officer", "2022-04-11", "Monday",  "16:37", "16:41", "Present"),
    (4, "Patrick James Wogar",  "782zSt", "Program Officer",  "2022-04-11", "Monday",   "16:37", "16:41", "Present"),
    (5, "Patience Ntishor",     "7xNpYG", "Finance Officer",  "2022-04-12", "Tuesday",  "15:20", "15:22", "Present"),
    (6, "Cletus Igbe",          "l5Vu2R", "IT Officer",       "2022-04-15", "Friday",   "21:19", "21:21", "Present"),
]


class BFEASApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Biometric Fingerprint Employee Attendance System")
        self.geometry("1360x740")
        self.configure(fg_color=BODY_BG)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_topbar()
        self._build_sidebar()
        self._build_main()

    # ---------------------------------------------------------- Top bar
    def _build_topbar(self):
        topbar = ctk.CTkFrame(self, fg_color=HEADER_BLUE, height=56, corner_radius=0)
        topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(1, weight=1)

        menu_btn = ctk.CTkLabel(topbar, text="\u2630", text_color="white",
                                 font=ctk.CTkFont(size=18))
        menu_btn.grid(row=0, column=0, padx=(18, 6), pady=10)

        title = ctk.CTkLabel(topbar, text="Biometric Fingerprint Employee Attendance System",
                              text_color="white", font=ctk.CTkFont(size=15, weight="bold"))
        title.grid(row=0, column=1, sticky="w", pady=10)

        profile_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        profile_frame.grid(row=0, column=2, sticky="e", padx=18)
        avatar = ctk.CTkLabel(profile_frame, text="\U0001F464", fg_color="white",
                               text_color=HEADER_BLUE, width=28, height=28,
                               corner_radius=14, font=ctk.CTkFont(size=14))
        avatar.grid(row=0, column=0, padx=(0, 8))
        ctk.CTkLabel(profile_frame, text="Cletus Igbe", text_color="white",
                     font=ctk.CTkFont(size=13)).grid(row=0, column=1)

    # ---------------------------------------------------------- Sidebar
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=SIDEBAR_BLUE, width=230, corner_radius=0)
        sidebar.grid(row=1, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        # Profile block
        profile = ctk.CTkFrame(sidebar, fg_color=SIDEBAR_BLUE, height=90)
        profile.pack(fill="x", pady=(18, 6))
        avatar = ctk.CTkLabel(profile, text="\U0001F464", fg_color="#cfd8e3",
                               text_color=SIDEBAR_BLUE, width=54, height=54,
                               corner_radius=27, font=ctk.CTkFont(size=24))
        avatar.pack()
        ctk.CTkLabel(profile, text="Cletus Igbe", text_color="white",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(6, 0))
        status = ctk.CTkFrame(profile, fg_color=SIDEBAR_BLUE)
        status.pack()
        ctk.CTkLabel(status, text="\u25CF", text_color="#3ddc63",
                     font=ctk.CTkFont(size=10)).pack(side="left")
        ctk.CTkLabel(status, text=" Online", text_color="#cfe0f0",
                     font=ctk.CTkFont(size=11)).pack(side="left")

        ctk.CTkFrame(sidebar, fg_color=SIDEBAR_BLUE_LIGHT, height=1).pack(fill="x", pady=8)

        self._nav_button(sidebar, "\U0001F3E0  Dashboard", active=False)

        self._section_label(sidebar, "MANAGE")
        self._nav_button(sidebar, "\U0001F464  Employee", active=False)

        self._section_label(sidebar, "REPORTS")
        self._nav_button(sidebar, "\U0001F465  Attendance List", active=False)
        self._nav_button(sidebar, "\U0001F4C4  Attendance Report", active=True)

    def _section_label(self, parent, text):
        lbl = ctk.CTkLabel(parent, text=text, text_color="#7fa0bd",
                            font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
        lbl.pack(fill="x", padx=18, pady=(16, 4))

    def _nav_button(self, parent, text, active=False):
        fg = ACCENT_BLUE if active else SIDEBAR_BLUE
        hover = ACCENT_BLUE if active else SIDEBAR_BLUE_LIGHT
        btn = ctk.CTkButton(parent, text=text, anchor="w", fg_color=fg, hover_color=hover,
                             text_color="white", corner_radius=0, height=42,
                             font=ctk.CTkFont(size=13), command=lambda: None)
        btn.pack(fill="x")
        return btn

    # ---------------------------------------------------------- Main content
    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color=BODY_BG, corner_radius=0)
        main.grid(row=1, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)

        # Header row: "Reports" + breadcrumb
        header = ctk.CTkFrame(main, fg_color=BODY_BG)
        header.pack(fill="x", padx=30, pady=(22, 10))
        ctk.CTkLabel(header, text="Reports", text_color=TEXT_DARK,
                     font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text="\U0001F3E0  Home  >  Reports", text_color="#7a8794",
                     font=ctk.CTkFont(size=12)).pack(side="right")

        # Card containing the "+" button
        add_card = ctk.CTkFrame(main, fg_color=CARD_BG, corner_radius=8, border_width=1,
                                 border_color=BORDER)
        add_card.pack(fill="x", padx=30, pady=(0, 14))
        ctk.CTkButton(add_card, text="+", width=34, height=30, fg_color=ACCENT_BLUE,
                      hover_color="#265f96", font=ctk.CTkFont(size=16, weight="bold")
                      ).pack(anchor="w", padx=14, pady=14)

        # Filter card: From / To / View Reports
        filter_card = ctk.CTkFrame(main, fg_color=CARD_BG, corner_radius=8, border_width=1,
                                    border_color=BORDER)
        filter_card.pack(fill="x", padx=30, pady=(0, 14))
        inner = ctk.CTkFrame(filter_card, fg_color=CARD_BG)
        inner.pack(fill="x", padx=14, pady=14)

        ctk.CTkLabel(inner, text="From:", text_color=TEXT_DARK,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 6))
        self.from_entry = ctk.CTkEntry(inner, placeholder_text="yyyy-mm-dd", width=150)
        self.from_entry.pack(side="left", padx=(0, 18))

        ctk.CTkLabel(inner, text="To:", text_color=TEXT_DARK,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 6))
        self.to_entry = ctk.CTkEntry(inner, placeholder_text="yyyy-mm-dd", width=150)
        self.to_entry.pack(side="left", padx=(0, 18))

        ctk.CTkButton(inner, text="View Reports", fg_color=ACCENT_BLUE,
                      hover_color="#265f96", width=120,
                      command=self._on_view_reports).pack(side="left")

        # Table card
        table_card = ctk.CTkFrame(main, fg_color=CARD_BG, corner_radius=8, border_width=1,
                                   border_color=BORDER)
        table_card.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Show entries + Search row
        controls = ctk.CTkFrame(table_card, fg_color=CARD_BG)
        controls.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(controls, text="Show", text_color=TEXT_DARK).pack(side="left")
        self.show_var = tk.StringVar(value="10")
        show_menu = ctk.CTkOptionMenu(controls, values=["10", "25", "50", "100"],
                                       variable=self.show_var, width=70)
        show_menu.pack(side="left", padx=8)
        ctk.CTkLabel(controls, text="entries", text_color=TEXT_DARK).pack(side="left")

        ctk.CTkLabel(controls, text="Search:", text_color=TEXT_DARK).pack(side="right", padx=(8, 0))
        self.search_entry = ctk.CTkEntry(controls, width=200)
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_table())

        # Treeview table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("BFEAS.Treeview", background="white", fieldbackground="white",
                         rowheight=30, font=("Segoe UI", 10), borderwidth=0)
        style.configure("BFEAS.Treeview.Heading", font=("Segoe UI", 10, "bold"),
                         background="#f4f6f8", foreground=TEXT_DARK, relief="flat")
        style.map("BFEAS.Treeview", background=[("selected", "#dbeafe")])

        columns = ("no", "name", "empid", "title", "date", "day", "in", "out", "status")
        headers = ["No.", "Name", "Employee ID.", "Job Title", "Date", "Day",
                   "Time-In", "Time-Out", "Status"]

        tree_frame = ctk.CTkFrame(table_card, fg_color=CARD_BG)
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                  style="BFEAS.Treeview", height=10)
        widths = [40, 190, 110, 140, 100, 90, 90, 90, 90]
        for col, head, w in zip(columns, headers, widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._all_rows = SAMPLE_ROWS
        self._populate_table(self._all_rows)

        # Footer: showing X of Y + pagination
        footer = ctk.CTkFrame(table_card, fg_color=CARD_BG)
        footer.pack(fill="x", padx=16, pady=(0, 14))
        self.showing_label = ctk.CTkLabel(footer, text="", text_color="#5a6672",
                                           font=ctk.CTkFont(size=12))
        self.showing_label.pack(side="left")
        self._update_showing_label(len(self._all_rows))

        pagination = ctk.CTkFrame(footer, fg_color=CARD_BG)
        pagination.pack(side="right")
        ctk.CTkButton(pagination, text="Previous", width=80, fg_color="#e9edf1",
                      text_color=TEXT_DARK, hover_color="#dde3e8").pack(side="left", padx=2)
        ctk.CTkButton(pagination, text="1", width=32, fg_color=ACCENT_BLUE,
                      hover_color="#265f96").pack(side="left", padx=2)
        ctk.CTkButton(pagination, text="Next", width=60, fg_color="#e9edf1",
                      text_color=TEXT_DARK, hover_color="#dde3e8").pack(side="left", padx=2)

    def _populate_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)

    def _update_showing_label(self, count, total=None):
        total = total if total is not None else len(self._all_rows)
        self.showing_label.configure(text=f"Showing 1 to {count} of {total} entries")

    def _filter_table(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            filtered = self._all_rows
        else:
            filtered = [r for r in self._all_rows if query in " ".join(str(c).lower() for c in r)]
        self._populate_table(filtered)
        self._update_showing_label(len(filtered), len(self._all_rows))

    def _on_view_reports(self):
        # Placeholder: in the real app this would query by date range.
        self._filter_table()


if __name__ == "__main__":
    app = BFEASApp()
    app.mainloop()
