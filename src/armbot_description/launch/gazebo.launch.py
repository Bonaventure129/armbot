import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    armbot_dir = get_package_share_directory("armbot_description")
    ros_gz_sim_dir = get_package_share_directory("ros_gz_sim")

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=os.path.join(armbot_dir, "urdf", "armbot.urdf.xacro"),
        description="Absolute path to the robot xacro file",
    )

    # Lets Gazebo resolve package://armbot_description/meshes/...
    resource_path = os.pathsep.join(
        p for p in (
            os.environ.get("GZ_SIM_RESOURCE_PATH", ""),
            str(Path(armbot_dir).parent.resolve()),
        ) if p
    )
    gz_resource_path = SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", resource_path)

    robot_description = ParameterValue(
        Command(["xacro ", LaunchConfiguration("model"), " is_sim:=true"]),
        value_type=str,
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, "launch", "gz_sim.launch.py")
        ),
        launch_arguments=[("gz_args", "-r -v 4 empty.sdf")],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=["-topic", "robot_description", "-name", "armbot"],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    return LaunchDescription([
        model_arg,
        gz_resource_path,
        gazebo,
        robot_state_publisher_node,
        spawn_robot,
        clock_bridge,
    ])