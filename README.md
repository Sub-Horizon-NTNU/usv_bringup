# USV BRINGUP
This package contains a launch file for starting up the PX4 uXRCE-DDS bridge (via
`MicroXRCEAgent`) and the nodes. The autopilot is PX4 — there is **no MAVROS or
mavlink-router** in the loop; the only autopilot link is the uXRCE-DDS bridge exposing
`px4_msgs` `/fmu/*` topics. Additionally it starts up
[environment_estimator](https://github.com/Sub-Horizon-NTNU/environment_estimator),
[usv_controller](https://github.com/Sub-Horizon-NTNU/usv_controller),
[transform_broadcaster](https://github.com/Sub-Horizon-NTNU/transform_broadcaster) and the
`usv_teleop` joystick (manual override).

The PX4 bridge runs on the CubeOrange+ TELEM2 port @ 921600 (`UXRCE_DDS_CFG=102`, see
`selene.params`). Override the companion serial device/baud with the `px4_serial_dev` /
`px4_serial_baud` launch args. Disable the joystick with `manual_control:=false`.

## Install:
create a folder src/ and then clone the repositories below into it.
```console
git clone git@github.com:Sub-Horizon-NTNU/usv_bringup.git
git clone git@github.com:Sub-Horizon-NTNU/environment_estimator.git
git clone git@github.com:Sub-Horizon-NTNU/usv_controller.git
git clone git@github.com:Sub-Horizon-NTNU/transform_broadcaster.git
git clone git@github.com:Sub-Horizon-NTNU/object_msgs.git
git clone git@github.com:Sub-Horizon-NTNU/waypoint_msgs.git
git clone git@github.com:Sub-Horizon-NTNU/usv_mission_package.git
git clone git@github.com:Sub-Horizon-NTNU/usv_object_detector.git
# PX4 message definitions — MUST match the flashed firmware (PX4 v1.16):
git clone -b release/1.16 https://github.com/PX4/px4_msgs.git
```

`usv_teleop` (joystick manual override) lives alongside these packages. Also install the PX4
uXRCE-DDS agent (`MicroXRCEAgent`) and the ROS 2 `joy` driver (`apt install ros-$ROS_DISTRO-joy`).

### Creating virtual environment for **usv_object_detector**

```console
python3 -m venv venv
source venv/bin/activate
touch venv/COLCON_IGNORE

pip install --upgrade pip setuptools wheel 
pip install colcon-common-extensions
pip install catkin_pkg empy==3.3.4 lark pyyaml packaging numpy==1.26.4 opencv-python-headless==4.9.0.80 requests pyopengl cython

python /usr/local/zed/get_python_api.py

pip install numpy==1.26.4 --force-reinstall
```


## Build:
```console 
colcon build
```

## Run:
```console
ros2 launch usv_bringup usv_bringup.launch.py simulator_mode:=<true/false>
```

The **"simulator_mode"** parameter is used to distinguish between the simulated system and the actual system.


