# this part is to conduct the test of the first part of robot.py

from sorter import settings
from sorter.robot import connect , load_gripper_down, save_gripper_down

robot = connect()
print('connected to robot')

save_gripper_down(robot)

saved= load_gripper_down()
print('angles saved' , saved.roll, saved.pitch, saved.yaw) #to see 

robot.close_connection()
print('done')
