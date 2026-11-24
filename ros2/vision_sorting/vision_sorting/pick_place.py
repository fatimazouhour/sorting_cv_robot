import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from niryo_ned_ros2_interfaces.action import RobotMove, Tool
from niryo_ned_ros2_interfaces.msg import  ArmMoveCommand, CommandStatus , ToolCommand

class PickPlace(Node):
    def __init__(self):
        super().__init__('pick_place')
        self.declare_parameter('gripper_id',13)
        self.declare_parameter('gripper_speed',500)
        self.gripper_id = self.get_parameter('gripper_id').value
        self.gripper_speed= self.get_parameter('gripper_speed').value
        self.tool= ActionClient(self,Tool,'/niryo_robot_tools_commander/action_server')
        self.declare_parameter('park', [0.20, 0.0, 0.20])
        self.declare_parameter('gripper_rpy', [0.0, 1.57, 0.0])
        self.park = self.get_parameter('park').value
        self.gripper_rpy = self.get_parameter('gripper_rpy').value
        self.arm = ActionClient(self, RobotMove, '/niryo_robot_arm_commander/robot_action')       

    def gripper(self, cmd_type):
        goal = Tool.Goal()
        goal.cmd.cmd_type = cmd_type
        goal.cmd.tool_id = self.gripper_id
        goal.cmd.speed = self.gripper_speed
        return self.send(self.tool, goal)

    def move(self, xyz):
        goal = RobotMove.Goal()
        goal.cmd.cmd_type = ArmMoveCommand.POSE
        goal.cmd.position.x, goal.cmd.position.y, goal.cmd.position.z = xyz
        goal.cmd.rpy.roll, goal.cmd.rpy.pitch, goal.cmd.rpy.yaw = self.gripper_rpy
        return self.send(self.arm, goal)

    def send(self, client, goal):
        if not client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Robot not ready (is the driver running?)')
            return False
        goal_handle = self.wait(client.send_goal_async(goal))
        result = self.wait(goal_handle.get_result_async()).result
        self.get_logger().info(result.message)
        return result.status == CommandStatus.SUCCESS

    def wait(self, future):
        rclpy.spin_until_future_complete(self, future)
        return future.result()



def main(args=None):
    rclpy.init(args=args)
    node = PickPlace()
    node.gripper(ToolCommand.OPEN_GRIPPER)
    node.move(node.park)  
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()