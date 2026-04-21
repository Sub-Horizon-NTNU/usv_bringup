
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, ExecuteProcess, RegisterEventHandler

from launch.actions import ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource
import os

#Mavros
mavros_dir = get_package_share_directory("mavros")

qgc_ip_arg = DeclareLaunchArgument("qgc_ip",default_value="127.0.0.1:14560")

#Mavros could be used for the same purpose, but it is much slower
mavlink_routerd = ExecuteProcess(
    cmd=["mavlink-routerd","-e", "127.0.0.1", "-e", LaunchConfiguration("qgc_ip"), "/dev/ttyACM0"],
    output='screen',
    shell=True
)

#For using Ardupilot DDS
micro_ros_agent = ExecuteProcess(
    cmd=["ros2 run micro_ros_agent micro_ros_agent serial -D /dev/ttyUSB0 -b 1500000"],
    output="screen",
    shell=True
)

def generate_launch_description():
    fcu_url_arg = DeclareLaunchArgument("fcu_url",default_value="udp://127.0.0.1:14550@14555")
    mavros_launch = IncludeLaunchDescription(
    XMLLaunchDescriptionSource(
        PathJoinSubstitution([mavros_dir, "launch/apm.launch"])
    ),
    launch_arguments={
        "fcu_url": LaunchConfiguration("fcu_url")
    }.items()
    )
    # Give mavros some time:
    delayed_mavros_launch = TimerAction(
        period=7.0,
        actions=[mavros_launch]
    )
   
    return LaunchDescription([
        qgc_ip_arg,
        micro_ros_agent,
       fcu_url_arg,
        mavlink_routerd,
       delayed_mavros_launch
    ])
