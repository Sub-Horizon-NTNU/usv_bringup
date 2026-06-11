#!/usr/bin/env python3
"""Print PX4 STATUSTEXT + arming state over MAVLink (USB) — no QGC.

Run this on the Cube's USB while you try to arm: PX4 prints the human-readable
reason ("Arming denied: ...") here. Far faster than guessing from failsafe_flags.

Usage:
    python3 mav_monitor.py [device]     # default /dev/ttyACM0
"""
import sys
from pymavlink import mavutil

dev = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"

m = mavutil.mavlink_connection(dev, baud=115200)
m.wait_heartbeat()
print(f"connected to {dev}. Watching STATUSTEXT + arming (Ctrl-C to stop)\n")

armed_prev = None
while True:
    msg = m.recv_match(type=["STATUSTEXT", "HEARTBEAT"], blocking=True)
    if msg.get_type() == "STATUSTEXT":
        print(f"[{msg.severity}] {msg.text}")
    else:  # HEARTBEAT
        armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        if armed != armed_prev:
            print(f"--- {'ARMED' if armed else 'DISARMED'} ---")
            armed_prev = armed
