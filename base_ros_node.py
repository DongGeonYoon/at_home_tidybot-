import math
import numpy as np

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from geometry_msgs.msg import Pose2D
from nav_msgs.msg import Odometry

from base_server import BaseManager
from constants import BASE_RPC_HOST, BASE_RPC_PORT, RPC_AUTHKEY


class TidyBotBaseROS(Node):

    def __init__(self):
        super().__init__('tidybot_base_node')

        # -----------------------------------
        # RPC connection
        # -----------------------------------
        host = BASE_RPC_HOST

        if host in ['', '0.0.0.0', '::']:
            host = '127.0.0.1'

        self.get_logger().info(
            f'Connecting to base RPC: '
            f'{host}:{BASE_RPC_PORT}'
        )

        self.manager = BaseManager(
            address=(host, BASE_RPC_PORT),
            authkey=RPC_AUTHKEY
        )

        self.manager.connect()

        self.get_logger().info(
            'Connected to base_server'
        )

        #self.base = self.manager.Base()
        self.base = self.manager.Base(max_vel=(0.5, 0.5, 1.57), max_accel=(1.0, 1.0, 3.14))
        # low-level controller 시작
        self.get_logger().info(
            'Resetting base controller...'
        )

        self.base.reset()

        self.get_logger().info(
            'Base controller ready'
        )

        # ===================================
        # /cmd_vel subscriber
        # ===================================
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # ===================================
        # 기존 position target
        # ===================================
        self.target_pose_sub = self.create_subscription(
            Pose2D,
            '/tidybot/base/target_pose',
            self.target_pose_callback,
            10
        )

        # ===================================
        # 기존 base state
        # ===================================
        self.state_pub = self.create_publisher(
            Pose2D,
            '/tidybot/base/state',
            10
        )

        # ===================================
        # Wheel odometry
        # ===================================
        self.odom_pub = self.create_publisher(
            Odometry,
            '/odom',
            10
        )

        # 20 Hz
        self.state_timer = self.create_timer(
            0.05,
            self.publish_state
        )

        self.get_logger().info(
            'Subscribed: /cmd_vel'
        )

        self.get_logger().info(
            'Subscribed: /tidybot/base/target_pose'
        )

        self.get_logger().info(
            'Publishing: /tidybot/base/state'
        )

        self.get_logger().info(
            'Publishing: /odom'
        )

    # =======================================
    # Velocity control
    # =======================================

    def cmd_vel_callback(self, msg):

        velocity = np.array(
            [
                msg.linear.x,
                msg.linear.y,
                msg.angular.z
            ],
            dtype=np.float64
        )

        try:
            self.base.execute_velocity(velocity)

        except Exception as e:
            self.get_logger().error(
                f'Failed to send velocity: {e}'
            )

    # =======================================
    # Position control
    # =======================================

    def target_pose_callback(self, msg):

        target = np.array(
            [
                msg.x,
                msg.y,
                msg.theta
            ],
            dtype=np.float64
        )

        action = {
            'base_pose': target
        }

        try:
            self.base.execute_action(action)

        except Exception as e:
            self.get_logger().error(
                f'Failed to send pose target: {e}'
            )

    # =======================================
    # State / odometry
    # =======================================

    def publish_state(self):

        try:
            state = self.base.get_state()

            pose = np.asarray(
                state['base_pose'],
                dtype=np.float64
            ).reshape(-1)

            velocity = np.asarray(
                state['base_velocity'],
                dtype=np.float64
            ).reshape(-1)

            if len(pose) < 3:
                return

            # --------------------------------
            # Pose2D
            # --------------------------------
            pose_msg = Pose2D()

            pose_msg.x = float(pose[0])
            pose_msg.y = float(pose[1])
            pose_msg.theta = float(pose[2])

            self.state_pub.publish(pose_msg)

            # --------------------------------
            # Odometry
            # --------------------------------
            odom = Odometry()

            odom.header.stamp = (
                self.get_clock().now().to_msg()
            )

            odom.header.frame_id = 'odom'
            odom.child_frame_id = 'base_link'

            # Position
            odom.pose.pose.position.x = float(pose[0])
            odom.pose.pose.position.y = float(pose[1])
            odom.pose.pose.position.z = 0.0

            # yaw -> quaternion
            yaw = float(pose[2])

            odom.pose.pose.orientation.x = 0.0
            odom.pose.pose.orientation.y = 0.0
            odom.pose.pose.orientation.z = math.sin(yaw / 2.0)
            odom.pose.pose.orientation.w = math.cos(yaw / 2.0)

            # velocity
            if len(velocity) >= 3:

                odom.twist.twist.linear.x = float(
                    velocity[0]
                )

                odom.twist.twist.linear.y = float(
                    velocity[1]
                )

                odom.twist.twist.angular.z = float(
                    velocity[2]
                )

            self.odom_pub.publish(odom)

        except Exception as e:
            self.get_logger().error(
                f'Failed to publish state: {e}'
            )

    def close(self):

        try:
            self.base.close()

        except Exception:
            pass


def main(args=None):

    rclpy.init(args=args)

    node = None

    try:
        node = TidyBotBaseROS()

        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    except Exception as e:
        print(f'ERROR: {e}')

    finally:

        if node is not None:
            node.close()
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
