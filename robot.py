import json   #saves data to files 
import socket #checks if robot connected to network

import connection

#take the connection and position angles from pyniryo
from pyniryo import NiryoRobot, PoseObject 

#checking the connection
def connect():
    try: 
        socket.create_connection((connection.ROBOT_IP,40001),timeout=5).close()
    except OSError:
        raise SystemExit(
            f"no answer from robot"
        )


    # calibrating the robot
    robot = NiryoRobot(connection.ROBOT_IP)
    robot.calibrate_auto() # motor automatically go  to 0 position
    robot.update_tool() # detect which gripper is mounted on
    robot.enable_tcp(True) # position of tcp and not the wrist
    robot.set_learning_mode(False) #robot holding the position
    robot.set_arm_max_velocity(connection.ARM_SPEED) #speed limit

    return robot 

#recording gripper angle
#the robot knows where to go, i want to make it know how the gripper should turn

def save_gripper_down(robot):
    pose = robot.get_pose() #returns the current pose of the gripper

    with open(settings.GRIPPER_FILE,'w') as file: #writing mode , see doc
            json.dump(pose.to_dict(),file,indent=2)  #converts the pose object to a dictionry, written in json format
            #indent to make it readble easily


#reading the poses recorded
def  load_gripper_down():

     with open(settings.GRIPPER_FILE) as file: #open the file created above
          return PoseObject.from_dict(json.load(file))
    