# USV BRINGUP
This package contains a launch file for starting up ArduPilot DDS, MAVROS, and the nodes. Additionallly it starts up [environment_estimator](https://github.com/Sub-Horizon-NTNU/environment_estimator), [usv_controller](https://github.com/Sub-Horizon-NTNU/usv_controller) and [transform_broadcaster](https://github.com/Sub-Horizon-NTNU/transform_broadcaster).

## Install:
```console
mkdir src && cd src
git clone --recurse-submodules git@github.com:Sub-Horizon-NTNU/usv_bringup.git
cd ..
colcon build
```

## Update:
```console
git pull
git submodule update --init --recursive
```

## Run:
```console
ros2 launch usv_bringup usv_bringup.launch.py simulator_mode:=<true/false>
```

The **"simulator_mode"** parameter is used to distinguish between the simulated system and the actual system.


