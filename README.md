### USV LAUNCH PROGRAM
This package contains a launch file for starting up ArduPilot DDS, MAVROS, and the nodes: [environment_estimator](https://github.com/Sub-Horizon-NTNU/environment_estimator), [usv_controller](https://github.com/Sub-Horizon-NTNU/usv_controller) and [transform_broadcaster](https://github.com/Sub-Horizon-NTNU/transform_broadcaster).

```console
ros2 launch usv_bringup usv_bringup.launch.py simulator_mode:=<true/false>
```
The **"simulator_mode"** parameter is used to distinguish between the simulated system and the actual system.