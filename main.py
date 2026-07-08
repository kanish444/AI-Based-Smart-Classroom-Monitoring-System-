import sys
print("Starting...", flush=True)
sys.stdout.flush()

import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime
import os

from timing import is_class_time, get_current_period
from sleep_detection import check_sleep, should_send_alert, reset_tracker
from sms_alert import send_sleep_alert
from excel_handler import save_attendance

# ================================
# STUDENT DATABASE (Manual Entry)
# ================================
STUDENTS = {
    "21CS001": "kanish",
}

# ================================
# GOLD / DARK COLOR THEME
# ================================
BG_DARK = "#121212"        # near-black base
BG_CARD = "#1c1c1c"        # card background
BG_CARD2 = "#232323"       # inner panel background
ACCENT_GOLD = "#D4AF37"    # primary gold
ACCENT_GOLD_LIGHT = "#F4CE5A"  # bright gold / highlight
ACCENT_GREEN = "#4CAF50"   # success (present)
ACCENT_GREEN_DIM = "#2E6930"  # dim green for pulse effect
ACCENT_RED = "#E63946"     # alert / absent
ACCENT_AMBER = "#FF9F1C"   # secondary warm accent
TEXT_LIGHT = "#EDEDED"
TEXT_MUTED = "#9c9c9c"

GLOW_GOLD = "#D4AF37"
GLOW_RED = "#E63946"

FONT_TITLE = ("Consolas", 19, "bold")
FONT_HEAD = ("Consolas", 12, "bold")
FONT_BODY = ("Consolas", 10)
FONT_STAT = ("Consolas", 22, "bold")

# ================================
# GLOBAL VARIABLES
# ================================
attendance_marked = {}
sleep_alerts_log = []
running = False
cap = None

# HUD / animation state
scan_line_y = 0
scan_line_dir = 1
pulse_state = True  # toggles for LIVE indicator glow

# ================================
# TKINTER GUI SETUP
# ================================
root = tk.Tk()
root.title("AI Smart Classroom Monitor // GOLD EDITION")
root.geometry("1100x680")
root.configure(bg=BG_DARK)

def glow_frame(parent, glow_color=GLOW_GOLD, **kwargs):
    """Frame with a gold border to simulate a subtle glow effect."""
    return tk.Frame(
        parent,
        bg=BG_CARD,
        highlightbackground=glow_color,
        highlightcolor=glow_color,
        highlightthickness=1,
        **kwargs
    )

# ---------- TOP BAR ----------
top_bar = glow_frame(root, glow_color=GLOW_GOLD, height=70)
top_bar.pack(fill=tk.X, padx=10, pady=10)

title_label = tk.Label(
    top_bar,
    text="\u2726 AI SMART CLASSROOM MONITOR",
    font=FONT_TITLE,
    bg=BG_CARD,
    fg=ACCENT_GOLD
)
title_label.pack(side=tk.LEFT, padx=20, pady=15)

subtitle_label = tk.Label(
    top_bar,
    text="[ ATTENDANCE & ATTENTION SYSTEM — ONLINE ]",
    font=("Consolas", 9, "bold"),
    bg=BG_CARD,
    fg=ACCENT_GOLD_LIGHT
)
subtitle_label.pack(side=tk.LEFT, padx=(0, 20))

clock_label = tk.Label(
    top_bar,
    text="",
    font=("Consolas", 16, "bold"),
    bg=BG_CARD,
    fg=ACCENT_GOLD
)
clock_label.pack(side=tk.RIGHT, padx=20, pady=15)

# ---------- MAIN FRAME ----------
main_frame = tk.Frame(root, bg=BG_DARK)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# ---------- LEFT: CAMERA ----------
left_frame = tk.Frame(main_frame, bg=BG_DARK)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

camera_card = glow_frame(left_frame, glow_color=GLOW_GOLD, padx=10, pady=10)
camera_card.pack(fill=tk.BOTH, expand=True)

camera_title = tk.Label(
    camera_card,
    text="\u25c9 LIVE CAMERA FEED",
    font=FONT_HEAD,
    bg=BG_CARD,
    fg=ACCENT_GOLD,
    anchor="w"
)
camera_title.pack(fill=tk.X)

camera_label = tk.Label(camera_card, bg="#000000",
                         highlightbackground=ACCENT_GOLD,
                         highlightthickness=2)
camera_label.pack(pady=10)

# Live indicator + period row
indicator_row = tk.Frame(camera_card, bg=BG_CARD)
indicator_row.pack(fill=tk.X, pady=(5, 0))

live_indicator = tk.Label(
    indicator_row,
    text="\u25cf PAUSED",
    font=("Consolas", 11, "bold"),
    bg=BG_CARD,
    fg=ACCENT_RED
)
live_indicator.pack(side=tk.LEFT)

period_label = tk.Label(
    indicator_row,
    text="\U0001F4C5 Checking period...",
    font=("Consolas", 11, "bold"),
    bg=BG_CARD2,
    fg=ACCENT_GOLD_LIGHT,
    padx=12,
    pady=4,
    highlightbackground=ACCENT_GOLD,
    highlightthickness=1
)
period_label.pack(side=tk.RIGHT)

# ---------- RIGHT: INFO PANEL ----------
right_frame = tk.Frame(main_frame, bg=BG_DARK, width=320)
right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

# Stats cards row
stats_row = tk.Frame(right_frame, bg=BG_DARK)
stats_row.pack(fill=tk.X, pady=(0, 10))

def make_stat_card(parent, label_text, color):
    outer = glow_frame(parent, glow_color=color)
    outer.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

    # Colored top accent strip
    strip = tk.Frame(outer, bg=color, height=4)
    strip.pack(fill=tk.X, side=tk.TOP)

    inner = tk.Frame(outer, bg=BG_CARD, padx=10, pady=8)
    inner.pack(fill=tk.BOTH, expand=True)

    value_lbl = tk.Label(inner, text="0", font=FONT_STAT, bg=BG_CARD, fg=color)
    value_lbl.pack()
    name_lbl = tk.Label(inner, text=label_text, font=("Consolas", 9, "bold"), bg=BG_CARD, fg=TEXT_MUTED)
    name_lbl.pack()
    return value_lbl

present_value = make_stat_card(stats_row, "PRESENT", ACCENT_GREEN)
absent_value = make_stat_card(stats_row, "ABSENT", ACCENT_RED)
detected_value = make_stat_card(stats_row, "DETECTED", ACCENT_GOLD)

# Attendance card
attendance_card = glow_frame(right_frame, glow_color=GLOW_GOLD, padx=10, pady=10)
attendance_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

att_label = tk.Label(
    attendance_card,
    text="\u25a3 ATTENDANCE LOG",
    font=FONT_HEAD,
    bg=BG_CARD,
    fg=ACCENT_GOLD,
    anchor="w"
)
att_label.pack(fill=tk.X)

att_list_frame = tk.Frame(attendance_card, bg=BG_CARD)
att_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

att_scrollbar = tk.Scrollbar(att_list_frame)
att_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

attendance_list = tk.Listbox(
    att_list_frame,
    bg=BG_CARD2,
    fg=ACCENT_GREEN,
    font=FONT_BODY,
    selectbackground="#3a3320",
    bd=0,
    highlightthickness=0,
    yscrollcommand=att_scrollbar.set
)
attendance_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
att_scrollbar.config(command=attendance_list.yview)

# Alerts card
alert_card = glow_frame(right_frame, glow_color=GLOW_RED, padx=10, pady=10)
alert_card.pack(fill=tk.BOTH, pady=(0, 10))

alert_title = tk.Label(
    alert_card,
    text="\u26a0 SLEEP ALERTS",
    font=FONT_HEAD,
    bg=BG_CARD,
    fg=ACCENT_AMBER,
    anchor="w"
)
alert_title.pack(fill=tk.X)

alert_list = tk.Listbox(
    alert_card,
    bg=BG_CARD2,
    fg=ACCENT_RED,
    font=("Consolas", 9),
    height=4,
    bd=0,
    highlightthickness=0
)
alert_list.pack(fill=tk.X, pady=5)

# ---------- STATUS BAR ----------
status_label = tk.Label(
    root,
    text="SYSTEM STARTING...",
    font=("Consolas", 10, "bold"),
    bg=BG_CARD,
    fg=ACCENT_GOLD,
    anchor="w",
    padx=15,
    pady=8,
    highlightbackground=GLOW_GOLD,
    highlightthickness=1
)
status_label.pack(fill=tk.X, padx=10, pady=(0, 5))

# ---------- FOOTER CREDIT BAR ----------
footer_label = tk.Label(
    root,
    text="\u2726 GOLD EDITION  |  AI Smart Classroom Monitor  |  Built by Kanish \u2726",
    font=("Consolas", 8),
    bg=BG_DARK,
    fg=TEXT_MUTED,
    anchor="center",
    pady=4
)
footer_label.pack(fill=tk.X, padx=10, pady=(0, 8))

# ================================
# FUNCTIONS
# ================================

def update_clock():
    now = datetime.now().strftime("%I:%M:%S %p")
    clock_label.config(text=f"\u23f1 {now}")
    root.after(1000, update_clock)

def update_attendance_list():
    attendance_list.delete(0, tk.END)
    for reg, name in attendance_marked.items():
        attendance_list.insert(tk.END, f"\u2714 {reg} :: {name}")
    present_count = len(attendance_marked)
    total = len(STUDENTS)
    present_value.config(text=str(present_count))
    absent_value.config(text=str(total - present_count))
    detected_value.config(text=str(present_count))

def show_alert(message):
    timestamp = datetime.now().strftime("%I:%M %p")
    alert_list.insert(0, f"\u26a0 {timestamp} :: {message}")

def update_status(message):
    status_label.config(text=message)

def update_live_indicator(active):
    if active:
        live_indicator.config(text="\u25cf LIVE", fg=ACCENT_GREEN)
    else:
        live_indicator.config(text="\u25cf PAUSED", fg=ACCENT_RED)

def pulse_live_indicator():
    """Continuously pulse the LIVE indicator between bright/dim green when active."""
    global pulse_state
    if running and live_indicator.cget("text").strip() == "\u25cf LIVE":
        pulse_state = not pulse_state
        live_indicator.config(fg=ACCENT_GREEN if pulse_state else ACCENT_GREEN_DIM)
    root.after(500, pulse_live_indicator)

def draw_hud_overlay(frame, w, h):
    """Draw sci-fi HUD corner brackets + animated scan-line on the frame."""
    global scan_line_y, scan_line_dir

    bracket_len = 30
    thickness = 2
    color = (55, 175, 212)  # gold in BGR

    corners = [(0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)]
    for cx, cy, dx, dy in corners:
        cv2.line(frame, (cx, cy), (cx + dx * bracket_len, cy), color, thickness)
        cv2.line(frame, (cx, cy), (cx, cy + dy * bracket_len), color, thickness)

    # Animated scan-line
    cv2.line(frame, (0, scan_line_y), (w, scan_line_y), (90, 200, 230), 1)
    scan_line_y += scan_line_dir * 4
    if scan_line_y >= h or scan_line_y <= 0:
        scan_line_dir *= -1

    return frame

def camera_loop():
    global running, cap, attendance_marked

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    student_ids = list(STUDENTS.keys())

    while running:
        if not is_class_time():
            period = get_current_period()
            root.after(0, lambda: update_status(f"\u23f8 {period} — Monitoring paused"))
            root.after(0, lambda: update_live_indicator(False))
            root.after(0, lambda: period_label.config(text=f"\U0001F4C5 {period}"))
            reset_tracker()
            time.sleep(5)
            continue

        ret, frame = cap.read()
        if not ret:
            continue

        period = get_current_period()
        root.after(0, lambda: update_status(f"\U0001F7E1 Active — {period}"))
        root.after(0, lambda: update_live_indicator(True))
        root.after(0, lambda: period_label.config(text=f"\U0001F4C5 {period}"))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        for i, (x, y, w, h) in enumerate(faces):
            if i < len(student_ids):
                student_id = student_ids[i]
                student_name = STUDENTS[student_id]
            else:
                student_id = f"Unknown_{i}"
                student_name = "Unknown"

            # Gold box for recognized students, muted grey for unknown — BGR format
            color = (55, 175, 212) if student_name != "Unknown" else (110, 110, 110)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, student_name, (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            if student_id not in attendance_marked and student_name != "Unknown":
                attendance_marked[student_id] = student_name
                root.after(0, update_attendance_list)

            face_roi = frame[y:y+h, x:x+w]
            if face_roi.size > 0:
                is_sleeping, duration = check_sleep(face_roi, student_id)
                if is_sleeping and should_send_alert(student_id):
                    msg = f"{student_name} ({student_id}) sleeping!"
                    root.after(0, lambda m=msg: show_alert(m))
                    threading.Thread(
                        target=send_sleep_alert,
                        args=(student_name, student_id),
                        daemon=True
                    ).start()

        # HUD overlay: corner brackets + scan-line
        fh, fw = frame.shape[:2]
        frame = draw_hud_overlay(frame, fw, fh)

        # Overlay: time + present count on camera feed
        overlay_time = datetime.now().strftime("%I:%M:%S %p")
        cv2.putText(frame, overlay_time, (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Present: {len(attendance_marked)}/{len(STUDENTS)}", (10, 460),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (55, 175, 212), 2)

        # Show frame in tkinter
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((640, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.config(image=imgtk)

    cap.release()
    save_attendance(attendance_marked)
    root.after(0, lambda: update_status("\U0001F4BE Attendance saved! System stopped."))
    root.after(0, lambda: update_live_indicator(False))

def start_system():
    global running
    running = True
    thread = threading.Thread(target=camera_loop, daemon=True)
    thread.start()
def on_closing():
    global running
    running = False
    time.sleep(1)
    save_attendance(attendance_marked)
    print("\U0001F4BE Attendance saved!")
    root.destroy()

# ================================
# START
# ================================
root.protocol("WM_DELETE_WINDOW", on_closing)

update_clock()
update_attendance_list()
pulse_live_indicator()
root.after(1000, start_system)

root.mainloop()