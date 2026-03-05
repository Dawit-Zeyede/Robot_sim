from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    # your package directory
    pkg_share = get_package_share_directory('description')


    # Path to your RViz config
    rviz_config_file = os.path.join(
        pkg_share,
        'config',
        'slam.rviz'
    )

    # path to slam_params_file
    slam_params_file = os.path.join(
        pkg_share,
        'config',
        'slam.yaml'
    )

    return LaunchDescription([
        # SLAM Toolbox node
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'slam_params_file': slam_params_file
            }]
        ),

        # RViz2 node
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_file]
        )
    ])