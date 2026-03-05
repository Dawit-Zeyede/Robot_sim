from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('description')

    # Config files
    rviz_config_file = os.path.join(pkg_share, 'config', 'slam.rviz')
    slam_params_file = os.path.join(pkg_share, 'config', 'slam.yaml')
    nav2_params_file = os.path.join(pkg_share, 'config', 'nav2_mapping.yaml')

    # 1️⃣ SLAM Toolbox (mapping)
    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params_file, {'use_sim_time': True}]
    )

    
    # Static transform from base_link to lidar_link
    static_lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_static_tf',
        arguments=['0', '0', '0.5', '0', '0', '0', 'base_link', 'lidar_link']
    )

    # 2️⃣ Nav2 nodes (planner, controller, BT, behavior) delayed to let SLAM publish first TF
    delayed_nav2_nodes = TimerAction(
        period=5.0,  # wait 2 seconds
        actions=[
            Node(
                package='nav2_planner',
                executable='planner_server',
                name='planner_server',
                output='screen',
                parameters=[nav2_params_file, {'use_sim_time': True}]
            ),
            Node(
                package='nav2_controller',
                executable='controller_server',
                name='controller_server',
                output='screen',
                parameters=[nav2_params_file, {'use_sim_time': True}]
            ),
            Node(
                package='nav2_bt_navigator',
                executable='bt_navigator',
                name='bt_navigator',
                output='screen',
                parameters=[nav2_params_file, {'use_sim_time': True}]
            ),
            Node(
                package='nav2_behaviors',
                executable='behavior_server',
                name='behavior_server',
                output='screen',
                parameters=[nav2_params_file, {'use_sim_time': True}]
            ),
            Node(
                package='nav2_velocity_smoother',
                executable='velocity_smoother',
                name='velocity_smoother',
                output='screen',
                parameters=[nav2_params_file, {'use_sim_time': True}]
            ),
        ]
    )

    # 3️⃣ Lifecycle Manager
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': [
                'planner_server',
                'controller_server',
                'bt_navigator',
                'behavior_server'
            ]
        }]
    )



    # 4️⃣ Explore Lite
    # explore_node = Node(
    #     package='explore_lite',
    #     executable='explore',
    #     name='explore',
    #     output='screen',
    #     parameters=[{
    #         'use_sim_time': True,
    #         'planner_frequency': 0.5,
    #         'progress_timeout': 60.0,
    #         'visualize': True,
    #         'robot_base_frame': 'base_link',
    #         'costmap_topic': '/global_costmap/costmap',
    #         'costmap_updates_topic': '/global_costmap/costmap_updates',
    #         'min_frontier_size': 0.5
    #     }]
    # )

    # 5️⃣ RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file]
    )

    delayed_mission_manager = TimerAction(
        period=7.0,   # after Nav2 lifecycle activates
        actions=[
            Node(
                package='description',
                executable='mission_manager.py',
                name='mission_manager',
                output='screen',
                parameters=[{'use_sim_time': True}]
            )
        ]
    )
    return LaunchDescription([
        slam_node,
        static_lidar_tf,
        delayed_nav2_nodes,
        lifecycle_manager,
#        explore_node,
        delayed_mission_manager,
        rviz_node,
    ])