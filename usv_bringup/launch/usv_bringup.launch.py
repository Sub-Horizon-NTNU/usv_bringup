
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, ExecuteProcess, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import UnlessCondition, IfCondition
from launch.actions import ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

### Nodes (BOAT side only — usv_controller runs on the PC, not resolved here):
transform_broadcaster_dir = get_package_share_directory("transform_broadcaster")
environment_estimator_dir = get_package_share_directory("environment_estimator")
usv_object_detector_dir = get_package_share_directory("usv_object_detector")

# transform broadcaster####################################################################################################################
camera_offset_x_arg = DeclareLaunchArgument('camera_offset_x',default_value='0.0',description='camera coordinates (left) relative to USV NED')
camera_offset_y_arg = DeclareLaunchArgument('camera_offset_y',default_value='0.0',description='camera coordinates (left) relative to USV NED')
camera_offset_z_arg = DeclareLaunchArgument('camera_offset_z',default_value='0.0',description='camera coordinates (left) relative to USV NED')

transform_broadcaster_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution([transform_broadcaster_dir, "launch/transform_broadcaster.launch.py"])
    ),
    launch_arguments={
        "camera_offset_x": LaunchConfiguration("camera_offset_x"),
        "camera_offset_y": LaunchConfiguration("camera_offset_y"),
        "camera_offset_z": LaunchConfiguration("camera_offset_z")
    }.items()
)

transform_broadcaster_launch_list = [
    camera_offset_x_arg,
    camera_offset_y_arg,
    camera_offset_z_arg,
    transform_broadcaster_launch
]


# environment_estimator node#########################################################################################################
fov_arg = DeclareLaunchArgument('field_of_view', default_value='78.0', description= "Field of view for the usv in degrees")
max_radius_arg = DeclareLaunchArgument('max_radius', default_value='20.0', description= "Max detection radius in [m]")
min_radius_arg = DeclareLaunchArgument('min_radius', default_value='0.75', description= "Min detection radius in [m]")
simulator_mode_arg = DeclareLaunchArgument('simulator_mode', default_value='false', description="If the object detector in the simulator is being used: true")
    
environment_estimator_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution([environment_estimator_dir, "launch/environment_estimator.launch.py"])
    ),
    launch_arguments={
        "field_of_view": LaunchConfiguration("field_of_view"),
        "max_radius": LaunchConfiguration("max_radius"),
        "min_radius": LaunchConfiguration("min_radius"),
        "simulator_mode":LaunchConfiguration("simulator_mode")
    }.items()
)

environment_estimator_launch_list = [
    fov_arg,
    max_radius_arg,
    min_radius_arg,
    simulator_mode_arg,
    environment_estimator_launch
]


# NOTE: usv_controller runs on the OPERATOR PC (not the boat) — its launch lives
# in the usv_controller package and is started there, alongside light_state_publisher
# and the joystick teleop.

## Object detector

publish_image_arg = DeclareLaunchArgument('publish_image',default_value='false',description='Publish images to topic selene/object_detector/image | <true/false>')
model_arg = DeclareLaunchArgument('model',default_value='best.onnx',description='Select which model to use. e.g: best.onnx')

usv_object_detector_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution([usv_object_detector_dir, "launch/usv_object_detector.launch.py"])
    ),
    launch_arguments={
        "publish_image":LaunchConfiguration("publish_image"),
        "model":LaunchConfiguration("model")
    }.items(),
    condition=UnlessCondition(LaunchConfiguration("simulator_mode"))

)

usv_object_detector_launch_list = [
    publish_image_arg,
    model_arg,
    usv_object_detector_launch
]


# PX4 uXRCE-DDS bridge #####################################################
# PX4 replaces ArduPilot: no MAVROS, no mavlink-router. The only autopilot link
# is the uXRCE-DDS bridge (px4_msgs /fmu/* topics). Per selene.params the bridge
# runs on the CubeOrange+ TELEM2 port @ 921600 (UXRCE_DDS_CFG=102); the companion
# serial device for TELEM2 is exposed below as a launch arg.

px4_agent_cmd_arg = DeclareLaunchArgument(
    "px4_agent_cmd", default_value="MicroXRCEAgent",
    description="uXRCE-DDS agent binary name (snap may install it as 'micro-xrce-dds-agent')")
px4_serial_dev_arg = DeclareLaunchArgument(
    "px4_serial_dev", default_value="/dev/ttyUSB0",
    description="Companion-side serial device for the PX4 TELEM2 uXRCE-DDS link")
px4_serial_baud_arg = DeclareLaunchArgument(
    "px4_serial_baud", default_value="921600",
    description="Baud for the PX4 uXRCE-DDS serial link (must match SER_TEL2_BAUD)")

micro_xrce_agent = ExecuteProcess(
    cmd=[LaunchConfiguration("px4_agent_cmd"),
         " serial --dev ",
         LaunchConfiguration("px4_serial_dev"),
         " -b ",
         LaunchConfiguration("px4_serial_baud")],
    output="screen",
    shell=True,
    condition=UnlessCondition(LaunchConfiguration("simulator_mode"))
)

px4_dds_launch_list = [
    px4_agent_cmd_arg,
    px4_serial_dev_arg,
    px4_serial_baud_arg,
    micro_xrce_agent,
]
#######################################################

# Optional MAVLink bridge for QGC (setup/debug only) #######################
# Bridges the Cube's USB MAVLink (/dev/ttyACM0) to QGroundControl over UDP, so
# you can configure/arm/calibrate without plugging a laptop into the boat. Runs
# alongside the DDS bridge (different port). OFF by default — enable with
#   ros2 launch ... mavlink_router:=true
mavlink_router_arg = DeclareLaunchArgument(
    "mavlink_router", default_value="true",
    description="Bridge Cube USB MAVLink to QGC over UDP. Disable with mavlink_router:=false")
mavlink_router_endpoint_arg = DeclareLaunchArgument(
    "mavlink_router_endpoint", default_value="192.168.2.42:14550",
    description="QGC UDP endpoint ip:port (the operator PC running QGC)")
mavlink_router_dev_arg = DeclareLaunchArgument(
    "mavlink_router_dev", default_value="/dev/ttyACM0",
    description="Cube USB serial device for MAVLink")

mavlink_routerd = ExecuteProcess(
    cmd=["mavlink-routerd", "-e",
         LaunchConfiguration("mavlink_router_endpoint"),
         LaunchConfiguration("mavlink_router_dev")],
    output="screen",
    shell=True,
    condition=IfCondition(LaunchConfiguration("mavlink_router")),
)

mavlink_router_launch_list = [
    mavlink_router_arg,
    mavlink_router_endpoint_arg,
    mavlink_router_dev_arg,
    mavlink_routerd,
]
#######################################################

# NOTE: the joystick teleop (usv_teleop usv_teleop.launch.py) runs on the
# OPERATOR PC where the Xbox controller is plugged in — not on the boat.

# Status lights / relay DRIVER (boat side) #################################
# Subscribes selene/light_state (published by light_state_publisher on the PC,
# next to the controller) and drives the Raspberry Pi over LOCAL UDP. Runs on
# the boat so the Pi/relay is robust to the radio link. See pi_lights/.
status_lights_arg = DeclareLaunchArgument(
    "status_lights", default_value="true",
    description="Run the boat-side light/relay driver (selene/light_state -> Pi UDP)")
pi_ip_arg = DeclareLaunchArgument(
    "pi_ip", default_value="192.168.2.5",
    description="Raspberry Pi address on the boat LAN")

light_relay_driver_node = Node(
    package="usv_teleop",
    executable="light_relay_driver",
    name="light_relay_driver",
    output="screen",
    parameters=[{"pi_ip": LaunchConfiguration("pi_ip")}],
    condition=IfCondition(LaunchConfiguration("status_lights")),
)

status_lights_launch_list = [
    status_lights_arg,
    pi_ip_arg,
    light_relay_driver_node,
]
#######################################################

###Combine everything
#
# THIS LAUNCH = THE BOAT (companion + Cube + Pi). It runs only what must be on
# the boat: the uXRCE-DDS agent (Cube link), mavlink-router (Cube USB -> QGC),
# the transform broadcaster, perception, and the light/relay driver to the Pi.
#
# The OPERATOR PC runs separately (NOT here): usv_controller, the joystick
# teleop (usv_teleop usv_teleop.launch.py), and light_state_publisher. They
# reach the boat over DDS (same ROS_DOMAIN_ID).

launch_list = (
    transform_broadcaster_launch_list +
    environment_estimator_launch_list +
    px4_dds_launch_list +
    mavlink_router_launch_list +
    status_lights_launch_list      # boat-side light/relay driver
    #usv_object_detector_launch_list
)


def generate_launch_description():
    return LaunchDescription(launch_list)
