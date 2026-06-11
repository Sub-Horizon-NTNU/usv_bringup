#!/usr/bin/env python3
"""Selene relay + status lights — Raspberry Pi Zero 2W.

Dumb + fast: listens for a 1-byte UDP state packet from the companion and drives
4 GPIO outputs (relay, red, amber, green). No ROS, no PWM. If packets stop for
TIMEOUT seconds it fails safe: relay OPEN, red ON, amber/green OFF.

Packet: b"SL" + 1 byte, bit0=relay bit1=red bit2=amber bit3=green.

Run as a systemd service (see lights.service). Edit the pins + ACTIVE_HIGH to
match your wiring (set active_high=False for active-low relay/LED modules).
"""
import socket
from gpiozero import OutputDevice

UDP_PORT = 5005
TIMEOUT  = 0.5          # seconds with no packet -> failsafe
MAGIC    = b"SL"

# --- wiring (BCM pins). Use 9..27 ONLY: they default LOW at boot, so the relay
# stays OPEN during the seconds before this script runs. active_high=False for
# active-low relay/LED modules. (GPIO 0..8 are pull-UP = HIGH at boot -> unsafe.)
relay = OutputDevice(27, active_high=True,  initial_value=False)  # pin 13, open at boot
red   = OutputDevice(19, active_high=True,  initial_value=True)   # pin 35, red on at boot
amber = OutputDevice(13, active_high=True,  initial_value=False)  # pin 33
green = OutputDevice(22, active_high=True,  initial_value=False)  # pin 15

def failsafe():
    relay.off(); red.on(); amber.off(); green.off()

def apply(state_byte):
    relay.value = bool(state_byte & 0b0001)
    red.value   = bool(state_byte & 0b0010)
    amber.value = bool(state_byte & 0b0100)
    green.value = bool(state_byte & 0b1000)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    sock.settimeout(TIMEOUT)
    failsafe()
    while True:
        try:
            data, _ = sock.recvfrom(16)
        except socket.timeout:
            failsafe()                      # link lost -> safe state
            continue
        if len(data) >= 3 and data[:2] == MAGIC:
            apply(data[2])

if __name__ == "__main__":
    main()
