#test reachability

from sorter import settings
from sorter.robot import can_reach, connect, load_gripper_down, park , target

robot = connect()
gripper = load_gripper_down()

park(robot,gripper)

robot.move(target(0.5,0.0,0.15,gripper))
robot.move(target(0.25,0.0,0.1,gripper))

input(robot,gripper)
park(robot,gripper)
robot.close_connection()

print("done") #just to tell that the test finished