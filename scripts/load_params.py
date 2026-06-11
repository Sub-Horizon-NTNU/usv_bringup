#!/usr/bin/env python3
"""Load a PX4 .params file onto the flight controller over MAVLink (USB) — no QGC.

PX4 runs MAVLink on the Cube's USB CDC by default, so this works even with the
TELEM MAVLink instances disabled. Sets every param, verifies it, then reboots.

Usage:
    pip install pymavlink
    python3 load_params.py [device] [params_file]
    # defaults: /dev/ttyACM0  selene.params
"""
import sys
import time
from pymavlink import mavutil

dev  = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
path = sys.argv[2] if len(sys.argv) > 2 else "selene.params"


def load(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 5:
                continue
            # columns: mav_id comp_id NAME VALUE TYPE  (TYPE 6=INT32, 9=REAL32)
            out.append((p[2], float(p[3]), int(p[4])))
    return out


def set_param(m, name, value, ptype, retries=3):
    for _ in range(retries):
        m.mav.param_set_send(m.target_system, m.target_component,
                             name.encode(), value, ptype)
        deadline = time.time() + 1.0
        while time.time() < deadline:
            msg = m.recv_match(type="PARAM_VALUE", blocking=True, timeout=1.0)
            if msg and msg.param_id.strip("\x00") == name:
                return msg.param_value
    return None


def main():
    params = load(path)
    print(f"connecting to {dev} ...")
    m = mavutil.mavlink_connection(dev, baud=115200)
    m.wait_heartbeat()
    print(f"connected: system {m.target_system}, {len(params)} params to set\n")

    bad = []
    for name, value, ptype in params:
        got = set_param(m, name, value, ptype)
        ok = got is not None and abs(got - value) <= max(1e-3, abs(value) * 1e-4)
        print(f"  {name:18} = {value:<10g} {'ok' if ok else 'FAILED'}")
        if not ok:
            bad.append(name)

    print()
    if bad:
        print(f"!! {len(bad)} params did not confirm: {', '.join(bad)}")
        print("   re-run, or check the name/type.")
    else:
        print("all params set + verified.")

    print("rebooting flight controller ...")
    m.mav.command_long_send(m.target_system, m.target_component,
                            mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
                            0, 1, 0, 0, 0, 0, 0, 0)
    print("done.")


if __name__ == "__main__":
    main()
