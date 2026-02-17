import tkinter as tk
from tkinter import ttk

import pyautogui


class DialogManager:
    def __init__(self) -> None:
        self.root = None

    def _ensure_root(self) -> bool:
        if self.root:
            return True
        try:
            self.root = tk.Tk()
            self.root.withdraw()
            self.root.attributes("-topmost", True)
            return True
        except Exception:
            self.root = None
            return False

    def _center(self, window: tk.Toplevel, width: int = 620, height: int = 280) -> None:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = int((screen_w / 2) - (width / 2))
        y = int((screen_h / 2) - (height / 2))
        window.geometry(f"{width}x{height}+{x}+{y}")

    def _bring_to_front(self, dialog: tk.Toplevel) -> None:
        """
        Force dialog to front to avoid "hidden popup" behavior on macOS/Windows.
        """
        dialog.update_idletasks()
        dialog.deiconify()
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.focus_force()
        dialog.grab_set()
        # Keep always-on-top briefly, then release to avoid window-manager oddities.
        dialog.after(500, lambda: dialog.attributes("-topmost", True))

    def alert(self, text: str, title: str = "Info", button: str = "OK") -> str:
        if not self._ensure_root():
            return pyautogui.alert(text=text, title=title, button=button)
        result = {"value": button}
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        self._center(dialog)

        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text=text, wraplength=580, justify="left").pack(fill="both", expand=True, pady=(4, 16))
        ttk.Button(body, text=button, command=dialog.destroy).pack()
        self._bring_to_front(dialog)
        dialog.wait_window()
        return result["value"]

    def confirm(self, text: str, title: str = "Confirm", buttons: list[str] | None = None) -> str:
        buttons = buttons or ["OK", "Cancel"]
        if not self._ensure_root():
            return pyautogui.confirm(text=text, title=title, buttons=buttons)

        result = {"value": buttons[-1]}
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        self._center(dialog, height=320)

        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text=text, wraplength=580, justify="left").pack(fill="both", expand=True, pady=(4, 16))
        buttons_frame = ttk.Frame(body)
        buttons_frame.pack(fill="x")

        for b in buttons:
            ttk.Button(buttons_frame, text=b, command=lambda val=b: self._set_and_close(dialog, result, val)).pack(side="left", padx=4)

        self._bring_to_front(dialog)
        dialog.wait_window()
        return result["value"]

    def prompt(self, text: str, title: str = "Input", default: str = "", password: bool = False) -> str | None:
        if not self._ensure_root():
            return pyautogui.password(text=text, title=title, default=default, mask="*") if password else pyautogui.prompt(text=text, title=title, default=default)

        result = {"value": None}
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        self._center(dialog, height=340)

        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text=text, wraplength=580, justify="left").pack(fill="x", pady=(4, 10))
        entry = ttk.Entry(body, show="*" if password else "")
        entry.pack(fill="x", pady=(0, 16))
        entry.insert(0, default)
        entry.focus_set()

        buttons_frame = ttk.Frame(body)
        buttons_frame.pack(fill="x")
        ttk.Button(buttons_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=(0, 6))
        ttk.Button(buttons_frame, text="Submit", command=lambda: self._submit_prompt(dialog, result, entry)).pack(side="left")

        dialog.bind("<Return>", lambda _: self._submit_prompt(dialog, result, entry))
        self._bring_to_front(dialog)
        dialog.wait_window()
        return result["value"]

    @staticmethod
    def _set_and_close(dialog: tk.Toplevel, result: dict, value: str) -> None:
        result["value"] = value
        dialog.destroy()

    @staticmethod
    def _submit_prompt(dialog: tk.Toplevel, result: dict, entry: ttk.Entry) -> None:
        result["value"] = entry.get()
        dialog.destroy()


ui = DialogManager()
