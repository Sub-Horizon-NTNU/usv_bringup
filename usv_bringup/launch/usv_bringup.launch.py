
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

mavlink_routerd = ExecuteProcess(
    cmd=["mavlink-routerd", "-e", "127.0.0.1", "-e", LaunchConfiguration("qgc_ip"), "/dev/ttyACM0"],
    output='screen',
    shell=True
)

def generate_launch_description():
    fcu_url_arg = DeclareLaunchArgument("fcu_url",default_value="udp://127.0.0.1:14550@14555")
    #gcs_url_arg = DeclareLaunchArgument("gcs_url",default_value="udp://@127.0.0.1:14560")
    mavros_launch = IncludeLaunchDescription(
    XMLLaunchDescriptionSource(
        PathJoinSubstitution([mavros_dir, "launch/apm.launch"])
    ),
    launch_arguments={
        "fcu_url": LaunchConfiguration("fcu_url")
        #"gcs_url": LaunchConfiguration("gcs_url"),
    }.items()
    )
    # Give mavlink-routerd some time:
    delayed_mavros_launch = TimerAction(
        period=5.0,
        actions=[mavros_launch]
    )
   

    return LaunchDescription([
        qgc_ip_arg,
        fcu_url_arg,
        #gcs_url_arg,
        mavlink_routerd,
        delayed_mavros_launch
    ])