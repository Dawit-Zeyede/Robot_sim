from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os


def generate_launch_description():
    pkg_path = get_package_share_directory('description')
    urdf = os.path.join(pkg_path, 'urdf', 'wheeled.urdf.xacro')
    
    # Declare a launch argument for the world file
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_path, 'worlds', 'empty.world'),
        description='Gazebo world file'
    )
    
    world = LaunchConfiguration('world')
    
    return LaunchDescription([
        world_arg,
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('gazebo_ros'),
                    'launch',
                    'gazebo.launch.py'
                    )
            ),
            launch_arguments={'world': world}.items()
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[
                {'robot_description': Command(['xacro ', urdf])},
                {'use_sim_time': True}]
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-entity', 'wheeled_humanoid',
                       '-topic', 'robot_description']
        ),
        # Joint State Publisher for all non-drive joints
        #Node(
        #    package='joint_state_publisher',
        #    executable='joint_state_publisher',
        #    name='joint_state_publisher',
        #    parameters=[
        #        {'use_sim_time': True},
        #        {'robot_description': Command(['xacro ', urdf])}
        #    ]
        #)
    ]) 