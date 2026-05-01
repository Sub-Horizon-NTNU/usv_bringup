# USV BRINGUP
This package contains a launch file for starting up ArduPilot DDS, MAVROS, and the nodes. Additionallly it starts up [environment_estimator](https://github.com/Sub-Horizon-NTNU/environment_estimator), [usv_controller](https://github.com/Sub-Horizon-NTNU/usv_controller) and [transform_broadcaster](https://github.com/Sub-Horizon-NTNU/transform_broadcaster).

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
```

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


