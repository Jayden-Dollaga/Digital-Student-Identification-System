"""
WHS Work Attendance Dashboard
-----------------------------
A Python (customtkinter + tkinter Canvas) recreation of the "WHS" work
attendance admin dashboard mockup:
  - Left dark sidebar with logo, current user, and SE (staff) list
  - Top header bar with email / date / power button
  - "Work Attendance" card with a day-by-day check/cross grid
  - "Abnormal Attendance Record" cards with approve / not-approved actions
  - "Need Work" application form panel

Run with:  python whs_dashboard.py
Requires:  pip install customtkinter pillow
"""

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk
from datetime import datetime

# ----------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

BG = "#eef1f7"
SIDEBAR_BG = "#141b2d"
SIDEBAR_ROW_ACTIVE = "#232e4d"
CARD_BG = "#ffffff"
TEXT_DARK = "#2b2f42"
TEXT_GRAY = "#9aa1b5"
BLUE = "#3aa0ff"
BLUE_LIGHT = "#eaf4ff"
GREEN = "#3ecf8e"
GREEN_LIGHT = "#e6faf1"
RED = "#ff6b81"
RED_LIGHT = "#ffeef1"
ORANGE = "#ff8a5b"
WEEKEND_BG = "#fdf3e4"

APP_W, APP_H = 1320, 840

AVATAR_PALETTE = ["#7c8ce0", "#e07c9a", "#e0a97c", "#7cc7e0", "#a37ce0", "#7ce0a0"]


def make_circle_avatar(initials, color, size=72):
    """Generate a circular avatar PIL image with initials on a solid color."""
    scale = 4
    big = size * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, big, big), fill=color)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(big * 0.4)
        )
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initials, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((big - w) / 2 - bbox[0], (big - h) / 2 - bbox[1]),
        initials,
        font=font,
        fill="white",
    )
    img = img.resize((size, size), Image.LANCZOS)
    return img


class RoundedCard(ctk.CTkFrame):
    """Simple white rounded-corner card container."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", CARD_BG)
        kwargs.setdefault("corner_radius", 16)
        super().__init__(master, **kwargs)


# ----------------------------------------------------------------------
# Mock data (mirrors the layout of the mockup)
# ----------------------------------------------------------------------
STAFF = [
    ("YiwenTang", "yiwentang@contra..."),
    ("XinweiHe", "xinweihe@contra..."),
    ("ZhengJingYao", "zhengjingyao@contra..."),
    ("YiwenTang", "yiwentang@contra..."),
    ("XinweiHe", "xinweihe@contra..."),
    ("ZhengJingYao", "zhengjingyao@contra..."),
    ("YiwenTang", "yiwentang@contra..."),
]

DAYS_IN_MONTH = 31
WEEKEND_COLS = {9, 10, 23, 24}  # highlighted like the mockup

# status: "approve" (red X marks) / "not_approved" (green checks, one red)
ATTENDANCE_ROWS = [
    {
        "status": "Approve",
        "status_color": RED,
        "name": "YiwenTang",
        "marks": {d: "x" for d in range(1, 32) if d not in (2, 3)},
    },
    {
        "status": "Not Approved",
        "status_color": BLUE,
        "name": "XinweiHe",
        "marks": {d: "check" for d in list(range(4, 9)) + list(range(11, 16))
                  + list(range(18, 22)) + list(range(25, 30))},
    },
    {
        "status": "Not Approved",
        "status_color": BLUE,
        "name": "ZhengJingYao",
        "marks": {**{d: "check" for d in list(range(4, 9)) + list(range(11, 16))
                     + list(range(18, 22)) + list(range(25, 30))},
                  26: "x"},
    },
]

ABNORMAL_RECORDS = [
    {"name": "YiwenTang", "date": "June 22, 2018", "status": "Approve", "status_color": RED, "btn": "Approve", "btn_style": "red"},
    {"name": "XinweiHe", "date": "June 22, 2018", "status": "Not Approved", "status_color": BLUE, "btn": "Not Approved", "btn_style": "blue"},
    {"name": "YiwenTang", "date": "June 22, 2018", "status": "Not Approved", "status_color": BLUE, "btn": "Not Approved", "btn_style": "blue"},
    {"name": "XinweiHe", "date": "June 22, 2018", "status": "Not Approved", "status_color": BLUE, "btn": "Not Approved", "btn_style": "blue"},
]

SYSTEM_STATUS = [
    ("ESP32 Connected", True),
    ("Fingerprint Sensor Ready", True),
    ("Database Connected", True),
]

LAST_SCAN = {
    "time": "09:31:14 AM",
    "student": "Jayden R. Dollaga",
    "student_id": "2026-001",
    "status": "Present",
}


class WHSDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WHS - Work Attendance")
        self.geometry(f"{APP_W}x{APP_H}")
        self.configure(fg_color=BG)
        self.resizable(True, True)

        self._avatar_cache = []  # keep PhotoImage refs alive

        self._build_sidebar()
        self._build_main()

    # ------------------------------------------------------------------
    def _avatar(self, initials, color_idx=0, size=48):
        pil_img = make_circle_avatar(initials, AVATAR_PALETTE[color_idx % len(AVATAR_PALETTE)], size)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
        self._avatar_cache.append(ctk_img)
        return ctk_img

    # ------------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=230, fg_color=SIDEBAR_BG, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="WHS", text_color=BLUE,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(28, 18))

        avatar_img = self._avatar("CK", 0, size=76)
        ctk.CTkLabel(sidebar, image=avatar_img, text="", fg_color="transparent").pack(pady=(4, 8))

        ctk.CTkLabel(
            sidebar, text="ChrisKang", text_color="white",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack()

        ctk.CTkFrame(sidebar, fg_color="#2a3350", height=1).pack(fill="x", padx=20, pady=(18, 10))

        ctk.CTkLabel(
            sidebar, text="SE list", text_color=TEXT_GRAY,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=22, pady=(4, 6))

        list_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", width=210)
        list_frame.pack(fill="both", expand=True, padx=6)

        for i, (name, email) in enumerate(STAFF):
            row_bg = SIDEBAR_ROW_ACTIVE if i == 0 else "transparent"
            row = ctk.CTkFrame(list_frame, fg_color=row_bg, corner_radius=8)
            row.pack(fill="x", pady=3, padx=4)

            img = self._avatar(name[:2].upper(), i, size=38)
            ctk.CTkLabel(row, image=img, text="", fg_color="transparent").pack(
                side="left", padx=(8, 8), pady=8
            )

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="both", expand=True, pady=8)
            ctk.CTkLabel(
                text_col, text=name, text_color="white",
                font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
            ).pack(fill="x")
            ctk.CTkLabel(
                text_col, text=email, text_color=TEXT_GRAY,
                font=ctk.CTkFont(size=11), anchor="w"
            ).pack(fill="x")



        ctk.CTkLabel(
            sidebar, text="\u25c6 BEYONDSOFT", text_color="#3a4470",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="bottom", pady=16)

    # ------------------------------------------------------------------
    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.pack(side="left", fill="both", expand=True)

        pad = 22
        main.grid_columnconfigure(0, weight=1)

        # ---- Header bar --------------------------------------------------
        header = RoundedCard(main, height=64)
        header.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, 14))
        header.grid_propagate(False)

        # Left: mini logo + search bar
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=18, pady=10)

        logo_badge = ctk.CTkLabel(
            left, text="WHS", fg_color=BLUE, text_color="white",
            corner_radius=10, width=44, height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        logo_badge.pack(side="left", padx=(0, 14))

        search_box = ctk.CTkEntry(
            left, placeholder_text="\U0001F50D  Search students, records...",
            fg_color=BLUE_LIGHT, border_width=0, corner_radius=10,
            width=190, height=34, font=ctk.CTkFont(size=12)
        )
        search_box.pack(side="left")

        # Right: status pill + clock + notifications + user info + power
        info = ctk.CTkFrame(header, fg_color="transparent")
        info.pack(side="right", padx=18, pady=10)

        self.clock_label = self._pill(info, "", BLUE_LIGHT, TEXT_DARK)
        self.clock_label.pack(side="left", padx=5)
        self._tick_clock()

        self._pill(info, "\U0001F7E2  ESP32 Connected", GREEN_LIGHT, GREEN).pack(side="left", padx=5)

        # Notification bell with a small badge
        bell_wrap = ctk.CTkFrame(info, fg_color="transparent")
        bell_wrap.pack(side="left", padx=5)
        ctk.CTkLabel(
            bell_wrap, text="\U0001F514", fg_color="#f3f5fa", corner_radius=17,
            width=34, height=34, font=ctk.CTkFont(size=14)
        ).pack()
        ctk.CTkLabel(
            bell_wrap, text="2", fg_color=RED, text_color="white",
            corner_radius=8, width=16, height=16, font=ctk.CTkFont(size=9, weight="bold")
        ).place(relx=1.0, rely=0.0, anchor="ne")

        self._pill(info, "\u2709  ChrisKang@ea.com", BLUE_LIGHT, BLUE).pack(side="left", padx=5)
        self._pill(info, "\U0001F4C5  June 28, 2018", BLUE_LIGHT, BLUE).pack(side="left", padx=5)

        power_btn = ctk.CTkButton(
            info, text="\u23fb", width=34, height=34, corner_radius=17,
            fg_color=BLUE, hover_color="#2c8ce0", font=ctk.CTkFont(size=14)
        )
        power_btn.pack(side="left", padx=(10, 0))

        # ---- Work attendance card ----------------------------------------
        attendance_card = RoundedCard(main)
        attendance_card.grid(row=1, column=0, sticky="ew", padx=pad, pady=(0, 14))

        ctk.CTkLabel(
            attendance_card, text="Work Attendance", text_color=TEXT_DARK,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=18, pady=(14, 6))

        self._build_attendance_table(attendance_card)

        btn_row = ctk.CTkFrame(attendance_card, fg_color="transparent")
        btn_row.pack(anchor="w", padx=18, pady=(4, 16))
        ctk.CTkButton(
            btn_row, text="\u2714  Full Approval", fg_color=BLUE, hover_color="#2c8ce0",
            corner_radius=18, width=150, height=38, font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            btn_row, text="\u26a0  Need Work", fg_color=ORANGE, hover_color="#e87a4b",
            corner_radius=18, width=130, height=38, font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        # ---- Bottom row: abnormal records + need work form ----------------
        bottom = ctk.CTkFrame(main, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="nsew", padx=pad, pady=(0, pad))
        main.grid_rowconfigure(2, weight=1)
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_rowconfigure(0, weight=1)

        abnormal_card = RoundedCard(bottom)
        abnormal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self._build_abnormal_records(abnormal_card)

        right_col = ctk.CTkFrame(bottom, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")
        right_col.grid_rowconfigure(0, weight=4)
        right_col.grid_rowconfigure(1, weight=3)
        right_col.grid_columnconfigure(0, weight=1)

        need_work_card = RoundedCard(right_col)
        need_work_card.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        self._build_need_work_form(need_work_card)

        status_card = RoundedCard(right_col)
        status_card.grid(row=1, column=0, sticky="nsew")
        self._build_system_status(status_card)

    # ------------------------------------------------------------------
    def _tick_clock(self):
        now = datetime.now().strftime("\U0001F551  %I:%M:%S %p")
        self.clock_label.configure(text=now)
        self.after(1000, self._tick_clock)

    # ------------------------------------------------------------------
    def _pill(self, master, text, bg, fg):
        return ctk.CTkLabel(
            master, text=text, fg_color=bg, text_color=fg,
            corner_radius=14, font=ctk.CTkFont(size=11, weight="bold"),
            padx=10, pady=4
        )

    # ------------------------------------------------------------------
    def _build_attendance_table(self, parent):
        cell_w = 24
        name_col_w = 210
        n_days = DAYS_IN_MONTH
        canvas_w = name_col_w + n_days * cell_w + 20
        row_h = 30
        header_h = 24
        canvas_h = header_h + row_h * len(ATTENDANCE_ROWS) + 10

        canvas = tk.Canvas(parent, width=canvas_w, height=canvas_h, bg=CARD_BG,
                            highlightthickness=0)
        canvas.pack(fill="x", padx=18, pady=(0, 6))

        for d in range(1, n_days + 1):
            x = name_col_w + (d - 1) * cell_w
            if d in WEEKEND_COLS:
                canvas.create_rectangle(x, 0, x + cell_w, canvas_h, fill=WEEKEND_BG, width=0)
            canvas.create_text(x + cell_w / 2, header_h / 2, text=str(d),
                                fill=TEXT_GRAY, font=("Helvetica", 8))

        canvas.create_text(20, header_h / 2, text="Surgery", fill=TEXT_GRAY,
                            font=("Helvetica", 9, "bold"), anchor="w")
        canvas.create_text(110, header_h / 2, text="Name", fill=TEXT_GRAY,
                            font=("Helvetica", 9, "bold"), anchor="w")
        canvas.create_line(0, header_h, canvas_w, header_h, fill="#eef0f5")

        for r, row in enumerate(ATTENDANCE_ROWS):
            y = header_h + r * row_h
            yc = y + row_h / 2

            chip_color = row["status_color"]
            chip_bg = RED_LIGHT if chip_color == RED else BLUE_LIGHT
            canvas.create_oval(14, yc - 6, 26, yc + 6, fill=chip_bg, outline="")
            mark = "\u2715" if chip_color == RED else "\u2610"
            canvas.create_text(20, yc, text=mark, fill=chip_color, font=("Helvetica", 8, "bold"))
            canvas.create_text(32, yc, text=row["status"], fill=chip_color,
                                font=("Helvetica", 9, "bold"), anchor="w")

            canvas.create_text(110, yc, text=row["name"], fill=TEXT_DARK,
                                font=("Helvetica", 9), anchor="w")

            for d in range(1, n_days + 1):
                x = name_col_w + (d - 1) * cell_w + cell_w / 2
                mark_type = row["marks"].get(d)
                if mark_type == "check":
                    canvas.create_oval(x - 8, yc - 8, x + 8, yc + 8, fill=GREEN_LIGHT, outline="")
                    canvas.create_text(x, yc, text="\u2713", fill=GREEN, font=("Helvetica", 9, "bold"))
                elif mark_type == "x":
                    canvas.create_oval(x - 8, yc - 8, x + 8, yc + 8, fill=RED_LIGHT, outline="")
                    canvas.create_text(x, yc, text="\u2715", fill=RED, font=("Helvetica", 9, "bold"))

            if r < len(ATTENDANCE_ROWS) - 1:
                canvas.create_line(0, y + row_h, canvas_w, y + row_h, fill="#f3f4f8")

    # ------------------------------------------------------------------
    def _build_abnormal_records(self, parent):
        ctk.CTkLabel(
            parent, text="Abnormal Attendance Record", text_color=TEXT_DARK,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=18, pady=(14, 10))

        cards_row = ctk.CTkFrame(parent, fg_color="transparent")
        cards_row.pack(fill="both", expand=True, padx=14)

        for i, rec in enumerate(ABNORMAL_RECORDS):
            card = ctk.CTkFrame(cards_row, fg_color="#f8f9fc", corner_radius=12,
                                 border_width=1, border_color="#eef0f5")
            card.pack(side="left", fill="both", expand=True, padx=6, pady=4)

            img = self._avatar(rec["name"][:2].upper(), i, size=44)
            ctk.CTkLabel(card, image=img, text="", fg_color="transparent").pack(pady=(14, 6))

            ctk.CTkLabel(card, text=rec["name"], text_color=TEXT_DARK,
                         font=ctk.CTkFont(size=12, weight="bold")).pack()
            ctk.CTkLabel(card, text=rec["date"], text_color=TEXT_GRAY,
                         font=ctk.CTkFont(size=12)).pack(pady=(0, 10))

            for icon, label, color in [
                ("\u25a2", rec["status"], rec["status_color"]),
                ("\u2699", "Needwork", TEXT_GRAY),
                ("\u2611", "OOF today.", TEXT_GRAY),
            ]:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(anchor="w", padx=16, pady=2, fill="x")
                ctk.CTkLabel(row, text=icon, text_color=color,
                             font=ctk.CTkFont(size=11)).pack(side="left")
                ctk.CTkLabel(row, text="  " + label, text_color=color,
                             font=ctk.CTkFont(size=11, weight="bold" if color != TEXT_GRAY else "normal")
                             ).pack(side="left")

            btn_color = RED if rec["btn_style"] == "red" else BLUE
            btn_bg = RED_LIGHT if rec["btn_style"] == "red" else BLUE_LIGHT
            btn_icon = "\u2714  " if rec["btn_style"] == "red" else "\u23f3  "
            ctk.CTkButton(
                card, text=btn_icon + rec["btn"], fg_color=btn_bg, text_color=btn_color,
                hover_color=btn_bg, corner_radius=16, height=34,
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(pady=(10, 14), padx=16, fill="x")

        pag = ctk.CTkFrame(parent, fg_color="transparent")
        pag.pack(pady=(0, 14))
        ctk.CTkLabel(pag, text="\u2039", text_color=TEXT_GRAY,
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=4)
        for n in range(1, 11):
            active = n == 5
            ctk.CTkLabel(
                pag, text=str(n),
                fg_color=BLUE if active else "transparent",
                text_color="white" if active else TEXT_GRAY,
                corner_radius=10, width=20, height=20,
                font=ctk.CTkFont(size=10)
            ).pack(side="left", padx=2)
        ctk.CTkLabel(pag, text="\u203a", text_color=TEXT_GRAY,
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=4)

    # ------------------------------------------------------------------
    def _build_need_work_form(self, parent):
        ctk.CTkLabel(
            parent, text="Need Work", text_color=TEXT_DARK,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=18, pady=(12, 8))

        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=18)

        fields = [("\U0001F464", "Username"), ("\u26a0", "Category"), ("\U0001F4C5", "Date")]
        for icon, label in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{icon}  {label}", text_color=TEXT_GRAY, width=95, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(side="left")
            ctk.CTkEntry(row, fg_color=BLUE_LIGHT, border_width=0, corner_radius=8,
                         height=26).pack(side="left", fill="x", expand=True)

        reason_row = ctk.CTkFrame(form, fg_color="transparent")
        reason_row.pack(fill="both", expand=True, pady=(6, 6))
        ctk.CTkLabel(reason_row, text="\U0001F4DD  Reason", text_color=TEXT_GRAY, anchor="nw",
                     font=ctk.CTkFont(size=12)).pack(anchor="w")
        ctk.CTkTextbox(reason_row, fg_color=BLUE_LIGHT, corner_radius=8
                        ).pack(fill="both", expand=True, pady=(4, 0))

        ctk.CTkButton(
            parent, text="\U0001F4E8  Application", fg_color=BLUE, hover_color="#2c8ce0",
            corner_radius=18, height=36, font=ctk.CTkFont(size=12, weight="bold")
        ).pack(padx=18, pady=(0, 14), fill="x")

    # ------------------------------------------------------------------
    def _build_system_status(self, parent):
        ctk.CTkLabel(
            parent, text="System Status", text_color=TEXT_DARK,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=18, pady=(14, 10))

        for label, ok in SYSTEM_STATUS:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=3)
            dot_color = GREEN if ok else RED
            ctk.CTkLabel(row, text="\u25cf", text_color=dot_color,
                         font=ctk.CTkFont(size=12)).pack(side="left")
            ctk.CTkLabel(row, text="  " + label, text_color=TEXT_DARK,
                         font=ctk.CTkFont(size=12)).pack(side="left")

        ctk.CTkFrame(parent, fg_color="#eef0f5", height=1).pack(fill="x", padx=18, pady=(8, 8))

        ctk.CTkLabel(parent, text="Last Scan", text_color=TEXT_GRAY,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=18)
        ctk.CTkLabel(parent, text=LAST_SCAN["time"], text_color=TEXT_DARK,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(0, 6))

        info_grid = ctk.CTkFrame(parent, fg_color="#f8f9fc", corner_radius=10)
        info_grid.pack(fill="x", padx=18, pady=(0, 14))

        def info_row(label, value, value_color=TEXT_DARK):
            r = ctk.CTkFrame(info_grid, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(r, text=label, text_color=TEXT_GRAY,
                         font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkLabel(r, text=value, text_color=value_color,
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="right")

        info_row("Student", LAST_SCAN["student"])
        info_row("ID", LAST_SCAN["student_id"])
        info_row("Status", LAST_SCAN["status"], value_color=GREEN)


if __name__ == "__main__":
    app = WHSDashboard()
    app.mainloop()