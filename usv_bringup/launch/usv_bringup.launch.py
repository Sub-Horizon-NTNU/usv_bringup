
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, ExecuteProcess, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import UnlessCondition
from launch.actions import ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource

### Nodes:
transform_broadcaster_dir = get_package_share_directory("transform_broadcaster")
environment_estimator_dir = get_package_share_directory("environment_estimator")
usv_controller_dir = get_package_share_directory("usv_controller")

mavros_dir = get_package_share_directory("mavros")

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


# USV controller launch list############################################################################################################
yaw_kp_arg = DeclareLaunchArgument("yaw_kp", default_value="1.1", description="Yaw angular velocity controller Kp")
yaw_ki_arg = DeclareLaunchArgument("yaw_ki", default_value="0.4", description="Yaw angular velocity controller Ki")
yaw_kd_arg = DeclareLaunchArgument("yaw_kd", default_value="0.1", description="Yaw angular velocity controller Kd")

lin_kp_arg = DeclareLaunchArgument("lin_kp", default_value="1.0", description="Linear velocity controller Kp")
lin_ki_arg = DeclareLaunchArgument("lin_ki", default_value="0.0", description="Linear velocity controller Ki")
lin_kd_arg = DeclareLaunchArgument("lin_kd", default_value="0.0", description="Linear velocity controller Kd")

max_linear_velocity_arg = DeclareLaunchArgument("max_linear_velocity", default_value="5.0", description="Maximum linear velocity [m/s]")
max_angular_velocity_arg = DeclareLaunchArgument("max_angular_velocity", default_value="2.0", description="Maximum angular velocity [rad/s]")
braking_radius_arg = DeclareLaunchArgument("braking_radius", default_value="3.0", description="Distance away from position hold waypoint to start braking [m]")


usv_controller_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution([usv_controller_dir, "launch/usv_controller.launch.py"])
    ),
    launch_arguments={
        "yaw_kp": LaunchConfiguration("yaw_kp"),
        "yaw_ki": LaunchConfiguration("yaw_ki"),
        "yaw_kd": LaunchConfiguration("yaw_kd"),
        "lin_kp": LaunchConfiguration("lin_kp"),
        "lin_ki": LaunchConfiguration("lin_ki"),
        "lin_kd": LaunchConfiguration("lin_kd"),
        "max_linear_velocity": LaunchConfiguration("max_linear_velocity"),
        "max_angular_velocity": LaunchConfiguration("max_angular_velocity"),
        "braking_radius": LaunchConfiguration("braking_radius"),
    }.items(),
)

usv_controller_launch_list = [
    yaw_kp_arg,
    yaw_ki_arg,
    yaw_kd_arg,
    lin_kp_arg,
    lin_ki_arg,
    lin_kd_arg,
    max_linear_velocity_arg,
    max_angular_velocity_arg,
    braking_radius_arg,
    usv_controller_launch,
]
###################################################################################################





# MAVROS AND ArduPilot DDS #################################################


#
qgc_ip_arg = DeclareLaunchArgument("qgc_ip",default_value="127.0.0.1:14560")
#Mavros could be used for the same purpose, but it is much slower
mavlink_routerd = ExecuteProcess(
    cmd=["mavlink-routerd","-e", "127.0.0.1", "-e", LaunchConfiguration("qgc_ip"), "/dev/ttyACM0"],
    output='screen',
    shell=True,
    condition=UnlessCondition(LaunchConfiguration("simulator_mode"))
)
#For using Ardupilot DDS
micro_ros_agent = ExecuteProcess(
    cmd=["ros2 run micro_ros_agent micro_ros_agent serial -D /dev/ttyUSB0 -b 1500000"],
    output="screen",
    shell=True,
    condition=UnlessCondition(LaunchConfiguration("simulator_mode"))
)

fcu_url_arg = DeclareLaunchArgument("fcu_url",default_value="udp://127.0.0.1:14550@14555")
mavros_launch = IncludeLaunchDescription(
XMLLaunchDescriptionSource(
    PathJoinSubstitution([mavros_dir, "launch/apm.launch"])
),
launch_arguments={
    "fcu_url": LaunchConfiguration("fcu_url")
}.items(),
condition=UnlessCondition(LaunchConfiguration("simulator_mode"))
)

# Give mavros some time:
delayed_mavros_launch = TimerAction(
    period=7.0,
    actions=[mavros_launch]
)

mavros_ardupilot_dds_launch_list = [
    qgc_ip_arg,
    micro_ros_agent,
    fcu_url_arg,
    mavlink_routerd,
    delayed_mavros_launch
]
#######################################################

###Combine everything

launch_list = (
    transform_broadcaster_launch_list +
    environment_estimator_launch_list +
    usv_controller_launch_list +
    mavros_ardupilot_dds_launch_list
)


def generate_launch_description():
    return LaunchDescription(launch_list)
