# Selene USV — ArduPilot → PX4 Migration Guide

This guide takes the Selene USV (CubeOrange+) from ArduPilot to **PX4 v1.16**, using only the
**uXRCE-DDS bridge** (no MAVROS, no mavlink-router). It covers building, flashing, sensor
bring-up, running the stack, and manual joystick control.

> **Read the order of battle first.** Steps 1–4 (firmware + state estimate) are fully covered
> by `selene.params` and are independently testable. Step 5 (the boat actually moving under
> offboard) needs **actuator/offboard params that are NOT yet in `selene.params`** — do that
> last, in SITL first, then on water with a safety plan.

---

## 0. Architecture: what changed and why

| | ArduPilot (old) | PX4 (new) |
|---|---|---|
| State IN | `ap/pose/filtered` (PoseStamped, ENU) via micro-ros | `/fmu/out/vehicle_odometry` (`px4_msgs/VehicleOdometry`, NED) via uXRCE-DDS |
| Commands OUT | `mavros/setpoint_velocity/cmd_vel` (TwistStamped) → MAVROS → MAVLink | `/fmu/in/{offboard_control_mode,trajectory_setpoint,vehicle_command}` (`px4_msgs`) |
| Autopilot link | micro-ros agent **+** MAVROS **+** mavlink-routerd | `MicroXRCEAgent` only |
| Manual control | RC / QGC | joystick over DDS (`usv_teleop` → `selene/manual/*`) |

**Data flow (PX4):**
```
PX4 (CubeOrange+, TELEM2 @921600)
  └─uXRCE-DDS─ MicroXRCEAgent ─ /fmu/out/vehicle_odometry (NED)
        └─ transform_broadcaster ─ TF world_ned→usv_ned
              └─ usv_controller (USVTransformHandler reads TF)
                    ├─ LOS guidance + PID  ─┐
                    │                         ├─► /fmu/in/trajectory_setpoint + offboard_control_mode
   usv_teleop (joystick) ─ selene/manual/* ─┘    + /fmu/in/vehicle_command (auto-arm / OFFBOARD)
```
The controller is the **single** node that talks to `/fmu/in/*`. Manual override just switches
which source feeds the setpoint stream, so handover never gaps (PX4 drops OFFBOARD if the
stream pauses > ~0.5 s).

---

## 1. Prerequisites (companion computer)

ROS 2 Humble, plus:

```bash
sudo apt update
sudo apt install ros-humble-joy
```

**PX4 uXRCE-DDS agent** (`MicroXRCEAgent`) — build from source. Do **not** pin an old tag:
the agent is a CMake superbuild that fetches and compiles its own Fast-DDS/Fast-CDR, and an
old release pulls dependency versions that fail to build on a current Humble toolchain (this
was the cause of the earlier build failure). Clone the latest release:

```bash
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent && mkdir build && cd build
cmake .. -DUAGENT_BUILD_EXECUTABLE=ON
make -j$(nproc)
sudo make install
sudo ldconfig /usr/local/lib/
```
Verify: `MicroXRCEAgent --help`.

> If `MicroXRCEAgent` isn't on `PATH` (or you install it under a different name), pass the
> binary to the bringup with `px4_agent_cmd:=/full/path/to/MicroXRCEAgent`.

---

## 2. Build the workspace

`usv_controller` and `transform_broadcaster` now depend on **`px4_msgs`**, which **must match the
flashed firmware** (PX4 v1.16):

```bash
cd ~/your_ws/src
git clone -b release/1.16 https://github.com/PX4/px4_msgs.git
# usv_teleop, usv_controller, transform_broadcaster, usv_bringup, waypoint_msgs, etc. live here too

cd ~/your_ws
colcon build
source install/setup.bash
```
> `px4_msgs` builds all message types and takes a few minutes the first time. If you later
> re-flash a different PX4 version, re-checkout the matching `px4_msgs` branch and rebuild.

---

## 3. Flash PX4 + load params

1. **Flash** PX4 v1.16 to the CubeOrange+ (`cubepilot_cubeorangeplus`) — easiest via
   QGroundControl → Vehicle Setup → Firmware → *Advanced* → PX4 v1.16, or from source:
   `make cubepilot_cubeorangeplus_default upload`.
2. **Load `selene.params`:** QGC → Parameters → Tools → **Load from file** → select
   `selene.params` → reboot.
3. **Confirm the DDS bridge config** (already in the file): `UXRCE_DDS_CFG=102` (TELEM2),
   `SER_TEL2_BAUD=921600`.
4. **Wiring:** the companion connects to CubeOrange+ **TELEM2**. Note which `/dev/tty*` the
   companion sees (e.g. `/dev/ttyUSB0`) — you'll pass it as `px4_serial_dev`.

---

## 4. Verify IMU / GPS / EKF2 (gate before any control)

Start just the agent:
```bash
MicroXRCEAgent serial --dev /dev/ttyUSB0 -b 921600
```
In another terminal (workspace sourced):
```bash
ros2 topic list | grep /fmu/out          # expect vehicle_odometry, vehicle_local_position, ...
ros2 topic echo /fmu/out/vehicle_odometry --once   # position[] + q[] populated, not NaN
```
In QGC, confirm:
- Septentrio dual-antenna GPS → **3D fix** and a valid **heading** (`SEP_YAW_OFFS=-31.14`).
- EKF2 converges; local NED origin set; no `mag`/`heading` errors (mag is disabled,
  `EKF2_MAG_TYPE=5`).

**Do not proceed to control until heading and position are trustworthy** — the LOS guidance is
meaningless with a bad heading.

---

## 5. Check the TF tree (transform_broadcaster)

```bash
ros2 launch usv_bringup usv_bringup.launch.py simulator_mode:=false \
     px4_serial_dev:=/dev/ttyUSB0 manual_control:=false
```
Then:
```bash
ros2 run tf2_ros tf2_echo world_ned usv_ned     # should track the boat
ros2 run tf2_tools view_frames                  # map→world_ned→usv_ned→camera
```
Drive the boat by hand / in SITL and confirm `usv_ned` translates and rotates correctly
(north = +x, east = +y, heading increases turning to starboard).

---

## 6. Manual joystick control (`usv_teleop`)

Plug in a joystick (`/dev/input/js0`) and launch with `manual_control:=true` (default).

**Default mapping (Xbox-style pad)** — change via params in
`usv_teleop/usv_teleop/joystick_teleop.py` or on the launch:

| Control | Default | Param |
|---|---|---|
| Forward/back (surge) | Left stick ↕ | `surge_axis=1`, `max_surge=2.0` m/s |
| Strafe (sway) | Left stick ↔ | `sway_axis=0`, `max_sway=1.0` m/s |
| Turn (yaw rate) | Right stick ↔ | `yaw_axis=3`, `max_yaw_rate=1.0` rad/s |
| **Deadman** (hold = manual) | LB | `deadman_button=4` |
| **E-stop** (disarm) | B | `estop_button=1` |

Find your indices with:
```bash
ros2 topic echo /joy        # press buttons / move sticks, read the array positions
```
Behaviour: **hold the deadman** → the boat follows the stick and ignores waypoints; **release**
→ LOS guidance resumes. **E-stop** → immediate disarm (latched; restart the controller to
re-enable auto-arm).

---

## 7. Autonomous / offboard mode (omni-X direct-actuator)

**Architecture:** Selene is a fixed-geometry **omni-X** — 4 azimuth pods locked at ±45°
(the ArduSub Lua only parked the steering servos; it did no dynamic allocation), 4 bidirectional
thrusters. PX4 has no airframe that allocates steerable pods, so the **velocity loop +
allocation run on the companion** and PX4 is used in **direct-actuator offboard**:

```
LOS guidance / joystick → desired body velocity → (×force gain) body wrench (Fx,Fy,Mz)
   → OmniXAllocator (4×3 pseudo-inverse) → 4 signed thrusts → ActuatorMotors
   → ActuatorServos held at the ±45° pattern (centered on e-stop)
```
The allocator (`usv_controller/include/usv_controller/OmniXAllocator.hpp`) is geometry-driven
via the params below. The controller **auto-arms and commands OFFBOARD** once actuator setpoints
have streamed ~0.5 s (10 ticks). Publish a waypoint and it follows the LOS path.

**Controller params to set for your boat** (`usv_controller`, e.g. via the launch or `ros2 param`):

| Param | Default | Meaning |
|---|---|---|
| `pod_half_length` | `0.5` | pod \|x\| from CG [m] — **set to real metres** |
| `pod_half_width` | `0.5` | pod \|y\| from CG [m] — **set to real metres** |
| `servo_angle_deg` | `45` | fixed azimuth angle |
| `max_thrust` | `30` | per-pod thrust [N] mapped to normalized ±1.0 |
| `surge_force_gain` | `10` | surge velocity → force (drag model; **tune on water**) |
| `sway_force_gain` | `10` | sway velocity → force |
| `yaw_force_gain` | `10` | yaw command → moment |
| `servo_command_norm` | `0.25` | normalized servo value for the ±45° offset (match PX4 servo min/max) |
| `relay_servo_index` | `6` | ActuatorServos idx for the **AUX3 safety relay** (−1 disables) |
| `light_red_servo_index` | `7` | ActuatorServos idx for AUX4 red (unarmed/relay off) |
| `light_amber_servo_index` | `4` | ActuatorServos idx for AUX5 amber (manual) |
| `light_green_servo_index` | `5` | ActuatorServos idx for AUX6 green (guided/auto) |

> **AUX3 safety relay — required or the boat is dead.** The relay gates power to *all*
> thrusters + azimuth servos. The controller drives it **HIGH when armed & not e-stopped**.
> Status lights are mutually exclusive: **red** = unarmed/relay-off, **amber** = manual,
> **green** = guided. PX4 side: map `AUX3→Servo7`, `AUX4→Servo8`, `AUX5→Servo5`, `AUX6→Servo6`,
> and **set the AUX3 output's disarmed/failsafe value LOW** so the relay defaults open
> (powered-off) on boot/disarm/link-loss. If thrusters get correct setpoints in the topics but
> don't move, the relay is open.

> The pod layout is baked in as `T1 front-port (+45°), T2 rear-port (−45°), T3 front-stbd
> (−45°), T4 rear-stbd (+45°)`, body x-fwd / y-stbd. Validated: surge `[+,+,+,+]`, sway
> `[+,−,−,+]`, yaw `[+,+,−,−]`. If a thruster drives the wrong way, reverse that ESC or flip
> the corresponding `ActuatorMotors` sign.

> ⚠️ **PX4 side (actuator day) — required before the boat moves.** `selene.params` is a GPS-day
> file with **no actuator/offboard params**. On a PX4 v1.16 reference still add:
> - **`COM_RCL_EXCEPT`** — allow OFFBOARD/arming **without RC** (else PX4 refuses to arm).
> - **Output mapping**: assign the 8 PWM outputs as `actuator_motor0–3` (ESC 1100–1900,
>   bidirectional) and `actuator_servo0–3` (500–2500, trim 1500). Set `CA_*`/output params so
>   the companion's `ActuatorMotors`/`ActuatorServos` indices land on the right physical outputs.
> - Confirm direct-actuator offboard is permitted; verify mapping + signs in **SITL first**.

**Test order:** SITL → bench (thrusters out of water / props off) → on water with a person ready
to hit E-stop.

---

## 8. Launch arguments (usv_bringup)

| Arg | Default | Meaning |
|---|---|---|
| `simulator_mode` | `false` | `true` skips the agent (SITL/sim provides DDS itself) |
| `px4_agent_cmd` | `MicroXRCEAgent` | agent binary name/path (override if not on `PATH`) |
| `px4_serial_dev` | `/dev/ttyUSB0` | companion serial for the TELEM2 DDS link |
| `px4_serial_baud` | `921600` | must match `SER_TEL2_BAUD` |
| `manual_control` | `true` | launch the joystick teleop |
| PID / LOS args | see launch file | `yaw_kp`, `lin_kp`, `lookahead_distance`, … (unchanged) |

```bash
ros2 launch usv_bringup usv_bringup.launch.py \
     simulator_mode:=false px4_serial_dev:=/dev/ttyUSB0 manual_control:=true
```

---

## 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| No `/fmu/out/*` topics | Agent not running / wrong `px4_serial_dev` / baud mismatch with `SER_TEL2_BAUD`. Check cabling to **TELEM2**. |
| Topics exist but `vehicle_odometry` is NaN | EKF2 not converged — fix GPS/heading first (step 4). |
| TF `world_ned→usv_ned` missing | transform_broadcaster not getting odometry, or QoS mismatch (it uses best-effort, matching PX4). |
| Boat won't arm in OFFBOARD | Missing `COM_RCL_EXCEPT` / actuator params; arming preflight failing (check QGC messages). |
| Boat drifts / wrong direction | Check heading sign and the NED velocity mapping; verify in SITL before water. |
| Joystick does nothing | Wrong button/axis indices — read `ros2 topic echo /joy`; confirm `/dev/input/js0`. |
| OFFBOARD drops mid-mission | Setpoint stream gapped — ensure the controller node stays alive at 20 Hz. |

---

## 10. Files changed in this migration

- `transform_broadcaster/include/broadcasters/DynamicFramePublisher.hpp` — VehicleOdometry sub
- `transform_broadcaster/{CMakeLists.txt,package.xml}` — `px4_msgs` dep
- `usv_controller/src/usv_controller/PositionController.cpp` + `.hpp` — PX4 direct-actuator offboard + omni-X allocation + manual mux
- `usv_controller/include/usv_controller/OmniXAllocator.hpp` — **new** fixed-geometry omni-X allocator
- `usv_controller/{CMakeLists.txt,package.xml}` — `px4_msgs`/`std_msgs` in, `mavros` out; `USVStates` dropped from build
- `usv_bringup/usv_bringup/launch/usv_bringup.launch.py` — agent-only + teleop, no MAVROS
- `usv_teleop/` — **new** joystick teleop package
- `selene.params` — PX4 GPS-day params (sensors + EKF2 + GPS + DDS); **actuator/offboard TBD**
