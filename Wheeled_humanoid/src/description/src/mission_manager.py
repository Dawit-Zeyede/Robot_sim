#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus

import tf2_ros
import tf2_geometry_msgs
from tf_transformations import quaternion_from_euler
import math


class MissionManager(Node):

    def __init__(self):
        super().__init__('mission_manager')

        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_callback,
            10
        )

        self.home_pose = None
        self.current_goal_handle = None
        self.state = "IDLE"

        self.timer = self.create_timer(2.0, self.initialize_home_pose)

        self.get_logger().info("Mission Manager started.")

    def initialize_home_pose(self):
        if self.home_pose is not None:
            return

        try:
            transform = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                rclpy.time.Time()
            )

            self.home_pose = PoseStamped()
            self.home_pose.header.frame_id = 'map'
            self.home_pose.pose.position.x = transform.transform.translation.x
            self.home_pose.pose.position.y = transform.transform.translation.y
            self.home_pose.pose.orientation = transform.transform.rotation

            self.get_logger().info("Home pose saved.")
        except Exception:
            pass

    def goal_callback(self, msg):
        self.get_logger().info("New goal received.")

        if self.current_goal_handle is not None:
            self.get_logger().info("Cancelling current goal...")
            self.current_goal_handle.cancel_goal_async()

        self.send_goal(msg)
        self.state = "GOING_TO_GOAL"

    def send_goal(self, pose):
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("Nav2 action server not available!")
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose

        send_goal_future = self.nav_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )

        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.current_goal_handle = future.result()

        if not self.current_goal_handle.accepted:
            self.get_logger().error("Goal rejected.")
            return

        self.get_logger().info("Goal accepted.")

        result_future = self.current_goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        status = future.result().status

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info("Goal reached!")

            if self.state == "GOING_TO_GOAL":
                self.get_logger().info("Returning to home...")
                self.state = "RETURNING_HOME"
                self.send_goal(self.home_pose)

            elif self.state == "RETURNING_HOME":
                self.get_logger().info("Returned home.")
                self.state = "IDLE"

        else:
            self.get_logger().warn("Goal failed or cancelled.")

    def feedback_callback(self, feedback):
        pass


def main(args=None):
    rclpy.init(args=args)
    node = MissionManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()