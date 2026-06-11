# Selene relay + status lights via Raspberry Pi Zero 2W

Skips PX4 for the lights/relay. The companion (ROS 2) decides the state and sends
a 1-byte UDP packet; the Pi drives 4 GPIO outputs. Clean digital on/off — no PWM,
no flicker, no Arduino. Fails safe (relay open, red on) if the link drops.

```
companion (ROS2)  --UDP "SL"+byte-->  Pi Zero  --GPIO-->  relay + red/amber/green
 light_state_sender.py                  lights.py
```

Packet byte bits: `bit0 relay, bit1 red, bit2 amber, bit3 green`.

## State → outputs
| State | relay | red | amber | green |
|---|---|---|---|---|
| disarmed / e-stop | open | **on** | off | off |
| armed + manual | closed | off | **on** | off |
| armed + auto (guided) | closed | off | off | **on** |

---

## 1. Raspberry Pi (Pi OS Lite)
```bash
sudo apt update && sudo apt install -y python3-gpiozero python3-lgpio
sudo mkdir -p /home/pi/pi_lights && sudo cp lights.py /home/pi/pi_lights/
sudo cp lights.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now lights.service
journalctl -u lights -f          # watch it
```

**Wiring (BCM pins, edit in `lights.py`):**

| Output | BCM | Physical pin |
|---|---|---|
| relay | GPIO27 | 13 |
| red | GPIO19 | 35 |
| amber | GPIO13 | 33 |
| green | GPIO22 | 15 |

All on the odd-pin row, all LOW at boot. GND: physical pin 9, 25, or 39. Common
ground with whatever drives the lamps/relay.

- **Use BCM 9-27 only.** They default LOW at boot, so the relay stays OPEN during
  the seconds before this script runs. **Avoid GPIO 0-8** (pull-UP = HIGH at boot
  -> relay would close), GPIO 2/3 (I2C, always high), 14/15 (serial console).
- **Relay safety:** also fit an external **10 kOhm pull-down** from the relay GPIO
  to GND, so the relay is open even when the Pi is off, booting, or crashed.
- Pi GPIO out is 3.3 V / ~16 mA — enough to switch a logic-level **relay module**
  and small LED drivers directly. For higher-current lamps, drive a transistor/
  MOSFET from the GPIO. Use a **relay/light module's own coil supply**, not the Pi.
- **Active-low modules** (most cheap relay boards turn on when the input is LOW):
  set `active_high=False` on that `OutputDevice(...)`.

Quick bench test without the companion:
```bash
# turn green + relay on:
python3 -c "import socket;socket.socket(2,2).sendto(b'SL'+bytes([0b1001]),('PI_IP',5005))"
```

## 2. Companion (Jetson, has ROS 2)
Set `PI_IP` at the top of `light_state_sender.py`, then run it alongside the stack:
```bash
python3 light_state_sender.py
# or add to a launch file / its own systemd service
```
It needs `px4_msgs` (already in your workspace) and the agent running so
`/fmu/out/vehicle_status` is available. No changes to `usv_controller`.

## Notes
- **Stop wiring AUX4–6 to the lights** — PX4 still emits PWM there, just leave it
  unconnected (or later remove the light/relay channels from the controller's
  `publish_actuators`). The relay AUX3 PWM is likewise unused now.
- The relay is now commanded from PX4's *real* `arming_state` (read by the sender),
  so it still follows actual arming — just routed Pi-side. **Keep the hardware
  E-stop independent** of this path.
- Failsafe: no packet for 0.5 s → relay open, red on. So a dead companion/network
  parks the boat safe.
