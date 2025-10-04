# main.py
"""
Nicolas Rewards System — Robust single-file build
- auto-recovers corrupted/empty data.json (backs it up)
- non-blocking rule audio playback (threaded)
- top-level windows reliably appear above main window
- logging to logs.txt
"""

import customtkinter as ctk
import json
import os
import threading
import pygame
from datetime import datetime
from shutil import move

# ===== CONFIG =====
DATA_FILE = "data.json"
LOG_FILE = "logs.txt"

RULES = [
    "1. No hitting or touching in any way that might hurt somebody else mentally or for real.",
    "2. Do NOT disrespect babysitters, parents, your siblings, or anybody in general.",
    "3. Do not under any circumstance, even if you are asked, throw ANYTHING, especially when you are told not to.",
    "4. When someone tells you to do something, DO IT without arguments.",
    "5. Stay in timeout when told!",
    "6. Follow all directions and rules from adults or whoever is watching you.",
    "7. Be safe. If something you are doing you don't think is safe, then DON'T do it!",
    "8. Other (not on this list)"
]

# ===== UTILITIES =====
def log_event(msg: str):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    # keep console visible for debugging
    print(line.strip())


def safe_load_data():
    """Load JSON; if file is empty or invalid, back it up and return fresh structure."""
    if not os.path.exists(DATA_FILE):
        return {"points": 0, "days": []}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            text = f.read()
            if not text.strip():
                raise ValueError("Empty file")
            return json.loads(text)
    except Exception as e:
        # backup the corrupt/empty file
        backup_name = f"data_corrupt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        try:
            move(DATA_FILE, backup_name)
            log_event(f"Bad data.json detected; backed up to {backup_name} ({e})")
        except Exception as mv_e:
            log_event(f"Failed to backup bad data.json: {mv_e}")
        # return a fresh structure
        return {"points": 0, "days": []}


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        log_event(f"Error saving data.json: {e}")


# ===== AUDIO HELPERS =====
pygame.mixer.init()  # initialize once at import time

def _play_with_soundobj(fullpath):
    """Try playing via Sound object (non-blocking)."""
    try:
        snd = pygame.mixer.Sound(fullpath)
        snd.play()
        return True
    except Exception:
        return False

def _play_with_music(fullpath):
    """Fallback using music module."""
    try:
        pygame.mixer.music.load(fullpath)
        pygame.mixer.music.play()
        return True
    except Exception:
        return False

def play_rule_audio(rule_index: int):
    """Play ruleN.mp3 (or whatever extension) in background. Threaded."""
    # candidate filenames (try common extensions)
    base = f"rule{rule_index + 1}"
    candidates = [f"{base}.mp3", f"{base}.wav", f"{base}.ogg"]
    # resolve full paths
    paths = [os.path.join(os.getcwd(), c) for c in candidates]
    existing = [p for p in paths if os.path.exists(p)]

    if not existing:
        log_event(f"Audio file missing for rule {rule_index+1} (tried {candidates})")
        return

    chosen = existing[0]

    def _play_job(path):
        ok = _play_with_soundobj(path)
        if not ok:
            ok = _play_with_music(path)
        if not ok:
            log_event(f"Playback failed for {os.path.basename(path)}")

    t = threading.Thread(target=_play_job, args=(chosen,), daemon=True)
    t.start()


# ===== APP =====
class RewardsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nicolas Rewards System")
        self.geometry("900x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # load or recover data
        self.data = safe_load_data()

        # ensure there is at least one day in data
        if not self.data.get("days"):
            self._start_new_day()
        else:
            self.current_day = self.data["days"][-1]

        # UI layout using grid for scaling
        self._setup_grid()
        self._build_ui()
        self.refresh_header()
        log_event("App launched")

    # --------- layout ----------
    def _setup_grid(self):
        self.grid_rowconfigure(0, weight=0)   # header
        self.grid_rowconfigure(1, weight=1)   # body
        self.grid_columnconfigure(0, weight=1)

    def _build_ui(self):
        # header
        self.header_frame = ctk.CTkFrame(self, corner_radius=8)
        self.header_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.header_label = ctk.CTkLabel(self.header_frame, text="", font=("Arial", 18, "bold"))
        self.header_label.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        # body / main buttons
        self.body_frame = ctk.CTkFrame(self, corner_radius=8)
        self.body_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        for i in range(3):
            self.body_frame.grid_columnconfigure(i, weight=1)
        self.body_frame.grid_rowconfigure(0, weight=1)
        self.body_frame.grid_rowconfigure(1, weight=0)

        # big buttons row
        btn_font = ("Arial", 16)
        ctk.CTkButton(self.body_frame, text="Strike Menu", font=btn_font,
                      command=self.open_strike_menu).grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkButton(self.body_frame, text="Exchange Menu", font=btn_font,
                      command=self.open_exchange_menu).grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkButton(self.body_frame, text="System Menu", font=btn_font,
                      command=self.open_system_menu).grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # quick action row
        ctk.CTkButton(self.body_frame, text="Tutorial", command=self.open_tutorial).grid(row=1, column=0, padx=10, pady=12, sticky="ew")
        ctk.CTkButton(self.body_frame, text="End Day", fg_color="red", command=self.end_day).grid(row=1, column=1, padx=10, pady=12, sticky="ew")
        ctk.CTkButton(self.body_frame, text="Refresh", command=self.refresh_header).grid(row=1, column=2, padx=10, pady=12, sticky="ew")

    # --------- header / state ----------
    def refresh_header(self):
        pts = self.data.get("points", 0)
        day_id = self.current_day.get("id", 0)
        strikes = len(self.current_day.get("strikes", []))
        date = self.current_day.get("date", "")
        self.header_label.configure(text=f"Day {day_id} | {date} | Strikes: {strikes} | Points: {pts}")

    # --------- core logic ----------
    def _start_new_day(self):
        next_id = len(self.data.get("days", [])) + 1
        new_day = {"id": next_id, "date": datetime.now().strftime("%Y-%m-%d"), "strikes": []}
        self.data.setdefault("days", []).append(new_day)
        self.current_day = new_day
        save_data(self.data)
        log_event(f"New day started (Day {next_id})")

    def start_new_day(self):
        # public wrapper for other code paths
        self._start_new_day()
        self.refresh_header()

    def end_day(self):
        strikes = len(self.current_day.get("strikes", []))
        if strikes < 3 and not self.current_day.get("point_awarded", False):
            # award point, but check day-level flag to avoid double-awarding
            self.data["points"] = self.data.get("points", 0) + 1
            self.current_day["point_awarded"] = True
            log_event(f"Day {self.current_day['id']} ended — +1 point awarded.")
        else:
            log_event(f"Day {self.current_day['id']} ended — no point (strikes: {strikes}).")
        save_data(self.data)
        # automatically start next day
        self._start_new_day()
        self.refresh_header()

    def add_strike_to_current(self, rule_index):
        if len(self.current_day.get("strikes", [])) >= 3:
            log_event("Strike limit reached for current day.")
            return
        rule_text = RULES[rule_index]
        strike = {"rule_index": rule_index, "reason": rule_text, "time": datetime.now().strftime("%H:%M:%S")}
        self.current_day.setdefault("strikes", []).append(strike)
        save_data(self.data)
        log_event(f"Strike recorded: {rule_text}")
        # play audio threaded, non-blocking
        play_rule_audio(rule_index)
        self.refresh_header()

    # --------- exchange / system ----------
    def redeem_points(self, cost, reward):
        pts = self.data.get("points", 0)
        if pts >= cost:
            self.data["points"] = pts - cost
            save_data(self.data)
            log_event(f"Redeemed {cost} points for {reward}.")
            self.refresh_header()
        else:
            log_event(f"Redeem failed (not enough points) for {reward}.")

    def manual_add_point(self):
        self.data["points"] = self.data.get("points", 0) + 1
        save_data(self.data)
        log_event("Manual +1 point (System).")
        self.refresh_header()

    def manual_remove_point(self):
        if self.data.get("points", 0) > 0:
            self.data["points"] = self.data.get("points", 0) - 1
            save_data(self.data)
            log_event("Manual -1 point (System).")
            self.refresh_header()

    def reset_system(self):
        # backup current data.json before resetting
        if os.path.exists(DATA_FILE):
            bk = f"data_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            try:
                move(DATA_FILE, bk)
                log_event(f"Reset: backed up data.json -> {bk}")
            except Exception as e:
                log_event(f"Reset: failed to backup data.json ({e})")
        self.data = {"points": 0, "days": []}
        save_data(self.data)
        log_event("System reset to default state.")
        self._start_new_day()
        self.refresh_header()

    # --------- windows (top-level) ----------
    def _make_toplevel(self, title, size="500x400"):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry(size)
        win.resizable(True, True)
        # attempt to ensure it stays above parent briefly, then allow normal stacking
        try:
            win.transient(self)
            win.lift()
            win.attributes("-topmost", True)
            win.focus_force()
            # clear topmost after a short delay to avoid permanent float
            self.after(250, lambda w=win: w.attributes("-topmost", False))
        except Exception:
            # older systems/window managers may ignore attributes — not fatal
            log_event("Top-level window could not set topmost/transient (ignored).")
        return win

    # --------- menu windows ----------
    def open_strike_menu(self):
        win = self._make_toplevel("Record a Strike", "700x500")
        ctk.CTkLabel(win, text="Select rule broken:", font=("Arial", 16, "bold")).pack(pady=10)
        # use scrollable frame to scale with many rules
        scroll = ctk.CTkScrollableFrame(win, width=660, height=380)
        scroll.pack(padx=10, pady=8, expand=True, fill="both")
        for i, rule in enumerate(RULES):
            ctk.CTkButton(scroll, text=rule, anchor="w",
                          command=lambda idx=i: self.add_strike_and_close(idx, win)).pack(fill="x", pady=6, padx=6)

    def add_strike_and_close(self, idx, win):
        self.add_strike_to_current(idx)
        # keep window open — babysitter may want to add more strikes; but if you prefer to close, do win.destroy()
        # we'll flash a small confirmation label instead
        # Optional: close after short delay:
        # self.after(250, win.destroy)

    def open_exchange_menu(self):
        win = self._make_toplevel("Exchange Points", "420x300")
        ctk.CTkLabel(win, text=f"Points available: {self.data.get('points',0)}", font=("Arial", 16, "bold")).pack(pady=12)
        ctk.CTkButton(win, text="Exchange 5 Points → Toy", command=lambda: [self.redeem_points(5, "Toy"), win.destroy()]).pack(pady=8, padx=12, fill="x")
        ctk.CTkButton(win, text="Exchange 10 Points → Hockey Game", command=lambda: [self.redeem_points(10, "Hockey Game"), win.destroy()]).pack(pady=8, padx=12, fill="x")

    def open_system_menu(self):
        win = self._make_toplevel("System Menu", "420x380")
        ctk.CTkLabel(win, text="Developer Tools", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkButton(win, text="Add Point", command=lambda: [self.manual_add_point(), win.focus_force()]).pack(pady=8, padx=12, fill="x")
        ctk.CTkButton(win, text="Remove Point", command=lambda: [self.manual_remove_point(), win.focus_force()]).pack(pady=8, padx=12, fill="x")
        ctk.CTkButton(win, text="Reset System", fg_color="red", command=lambda: [self.reset_system(), win.destroy()]).pack(pady=16, padx=12, fill="x")

    def open_tutorial(self):
        win = self._make_toplevel("Tutorial", "560x420")
        t = (
            "Quick tutorial — how to use\n\n"
            "1) Strike Menu: press the rule that was broken. The app logs time + reason and plays the rule audio if available.\n\n"
            "2) End Day: automatically awards +1 point if strikes < 3 and immediately starts the next day.\n\n"
            "3) Exchange Menu: redeem points (5 → Toy, 10 → Hockey game).\n\n"
            "4) System Menu: add/remove points or reset system (admins only).\n\n"
            "Everything is saved to data.json and all events logged to logs.txt."
        )
        ctk.CTkLabel(win, text=t, wraplength=520, justify="left").pack(padx=12, pady=12)

# ===== RUN =====
if __name__ == "__main__":
    app = RewardsApp()
    app.mainloop()
