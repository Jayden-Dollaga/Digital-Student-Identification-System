from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import customtkinter as ctk
from gui import app

orig_mainloop = ctk.CTk.mainloop
ctk.CTk.mainloop = lambda self: None

try:
    app.main()
    print("STARTUP_OK")
except Exception:
    import traceback

    traceback.print_exc()
    print("STARTUP_FAILED")
finally:
    ctk.CTk.mainloop = orig_mainloop
