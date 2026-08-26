import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog, messagebox

from core.database import (
    generate_statistics_report,
    generate_attendance_chart,
    generate_section_chart,
    generate_grade_chart,
)
from core.logger import log


def show_statistics_report(app):
    if not app.has_permission("export"):
        messagebox.showerror("Permission Denied", "Your role cannot view reports.", parent=app)
        return

    try:
        report_text = generate_statistics_report()

        dialog = ctk.CTkToplevel(app)
        dialog.title("Statistics Report")
        dialog.geometry("800x600")
        dialog.transient(app)
        dialog.grab_set()

        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(padx=16, pady=(16, 8), fill="x")
        ctk.CTkLabel(header, text="📊 Attendance Statistics Report", font=("Segoe UI", 16, "bold")).pack(anchor="w")

        text_widget = ctk.CTkTextbox(dialog, font=("Consolas", 10), wrap="none")
        text_widget.pack(padx=12, pady=(0, 12), fill="both", expand=True)
        text_widget.insert("1.0", report_text)
        text_widget.configure(state="disabled")

        button_row = ctk.CTkFrame(dialog, fg_color="transparent")
        button_row.pack(padx=16, pady=(0, 16), fill="x")
        button_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(button_row, text="Copy to Clipboard", width=150,
                      command=lambda: _copy_to_clipboard(app, report_text)).grid(row=0, column=0, padx=(0, 8), sticky="w")
        ctk.CTkButton(button_row, text="Close", width=150, fg_color="transparent",
                      border_width=1, command=dialog.destroy).grid(row=0, column=1, sticky="e")

        app.log_message("Statistics report generated")
    except Exception as exc:
        # SECURITY FIX: user-facing error used to include the raw exception
        # text (f"Could not generate report: {exc}"), which can leak
        # filesystem paths, database paths, or other internal details. The
        # detailed exception still goes to the log; the user only sees a
        # safe, generic message.
        log.error(f"Could not generate statistics report: {exc}")
        messagebox.showerror(
            "Report Error",
            "Unable to generate the report. Please check the application logs for more information.",
            parent=app,
        )


def export_statistics_report(app):
    if not app.has_permission("export"):
        messagebox.showerror("Permission Denied", "Your role cannot export reports.", parent=app)
        return

    try:
        report_text = generate_statistics_report()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            parent=app,
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as target_file:
            target_file.write(report_text)

        app.log_message(f"Report exported to {file_path}")
        messagebox.showinfo("Export Successful", f"Report saved to:\n{file_path}", parent=app)
    except Exception as exc:
        log.error(f"Could not export statistics report: {exc}")
        messagebox.showerror(
            "Export Error",
            "Unable to export the report. Please check the application logs for more information.",
            parent=app,
        )


def show_statistics_charts(app):
    if not getattr(app, 'PILLOW_AVAILABLE', False):
        messagebox.showwarning("Charts Not Available", "Pillow library is not installed. Install it with pip install pillow.", parent=app)
        return

    attendance_chart = None
    section_chart = None
    grade_chart = None

    try:
        attendance_chart = generate_attendance_chart()
        section_chart = generate_section_chart()
        grade_chart = generate_grade_chart()
    except Exception as exc:
        log.error(f"Could not generate statistics charts: {exc}")
        messagebox.showerror(
            "Chart Error",
            "Unable to generate the charts. Please check the application logs for more information.",
            parent=app,
        )
        return

    if not any([attendance_chart, section_chart, grade_chart]):
        messagebox.showwarning("No Data", "Insufficient data to generate charts. Ensure there are attendance records.", parent=app)
        return

    dialog = ctk.CTkToplevel(app)
    dialog.title("Statistics Charts")
    dialog.geometry("1000x700")
    dialog.transient(app)
    dialog.grab_set()

    header = ctk.CTkFrame(dialog, fg_color="transparent")
    header.pack(padx=16, pady=(16, 8), fill="x")
    ctk.CTkLabel(header, text="📈 Attendance Analytics Charts", font=("Segoe UI", 16, "bold")).pack(anchor="w")

    tabview = ctk.CTkTabview(dialog)
    tabview.pack(padx=12, pady=12, fill="both", expand=True)

    if attendance_chart:
        tabview.add("📅 Timeline")
        _display_chart_in_tab(tabview.tab("📅 Timeline"), attendance_chart)
    if section_chart:
        tabview.add("📊 By Section")
        _display_chart_in_tab(tabview.tab("📊 By Section"), section_chart)
    if grade_chart:
        tabview.add("🥧 By Grade")
        _display_chart_in_tab(tabview.tab("🥧 By Grade"), grade_chart)

    app.log_message("Charts displayed successfully")


def _display_chart_in_tab(tab, image_path):
    try:
        if not image_path:
            ctk.CTkLabel(tab, text="No chart available.").pack(padx=12, pady=12)
            return

        from PIL import Image, ImageTk
        image = Image.open(image_path)
        image.thumbnail((950, 600), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        label = ctk.CTkLabel(tab, image=photo, text="")
        label.image = photo
        label.pack(padx=12, pady=12, fill="both", expand=True)
    except Exception as exc:
        log.error(f"Could not load chart image: {exc}")
        ctk.CTkLabel(tab, text="Could not load chart. Check the application logs for more information.", text_color="red").pack(padx=12, pady=12)


def _copy_to_clipboard(app, text):
    try:
        app.clipboard_clear()
        app.clipboard_append(text)
        app.update()
        app.log_message("Report copied to clipboard")
    except Exception as exc:
        log.error(f"Could not copy report to clipboard: {exc}")
        messagebox.showerror(
            "Clipboard Error",
            "Unable to copy the report. Please check the application logs for more information.",
            parent=app,
        )
