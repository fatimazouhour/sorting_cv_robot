import threading

import rclpy
import roslibpy
import roslibpy.actionlib
from rclpy.action import ActionServer
from rclpy.node import Node
from rosidl_runtime_py import message_to_ordereddict

from niryo_ned_ros2_interfaces.action import RobotMove
from niryo_ned_ros2_interfaces.msg import CommandStatus


class NedCompat(Node):

    ACTION = '/niryo_robot_arm_commander/robot_action'

    def __init__(self):
        super().__init__('ned_compat')
        self.declare_parameter('robot_ip', '10.10.10.10')
        self.declare_parameter('rosbridge_port', 9090)
        self.declare_parameter('timeout', 60.0)
        robot_ip = self.get_parameter('robot_ip').value
        port = self.get_parameter('rosbridge_port').value
        self.timeout = self.get_parameter('timeout').value

        self.robot = roslibpy.Ros(host=robot_ip, port=port)
        self.robot.run(timeout=10)
        self.robot_action = roslibpy.actionlib.ActionClient(
            self.robot, self.ACTION, 'niryo_robot_arm_commander/RobotMoveAction')
        self.server = ActionServer(self, RobotMove, self.ACTION, self.execute_callback)
        self.get_logger().info(f'Forwarding {self.ACTION} to the robot at {robot_ip}')

    def execute_callback(self, goal_handle):
        cmd = message_to_ordereddict(goal_handle.request.cmd)
        cmd.pop('tcp_version')
        cmd.pop('trajectory')

        answer = {}
        done = threading.Event()

        def on_result(robot_result):
            answer.update(robot_result)
            done.set()

        goal = roslibpy.actionlib.Goal(self.robot_action, roslibpy.Message({'cmd': cmd}))
        goal.send(result_callback=on_result)

        result = RobotMove.Result()
        if not done.wait(self.timeout):
            goal.cancel()
            result.status = -1
            result.message = f'no answer from the robot after {self.timeout:.0f} s'
            goal_handle.abort()
            return result

        result.status = answer['status']
        result.message = answer['message']
        if result.status == CommandStatus.SUCCESS:
            goal_handle.succeed()
        else:
            goal_handle.abort()
        return result

    def close(self):
        self.robot.terminate()


def main(args=None):
    rclpy.init(args=args)
    node = NedCompat()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.close()
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()