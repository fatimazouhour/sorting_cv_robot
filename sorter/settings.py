import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env

#connection
ROBOT_IP = os.environ("ROBOT_IP")  
CAMERA = os.environ("CAMERA")
ROBOT_TYPE = os.environ.get("ROBOT_TYPE", "niryo")
#YOLO_MODEL = os.environ.get("YOLO_MODEL", "data/yolo11s.pt")

#arm
ARM_SPEED = 40 #percent of the maximum speed 
APPROACH_HEIGHT = 0.08 #go this much cm above the target
PARK_XYZ= [0.0,0.0,0.0] #park position for the arm, in meters
DROP_HEIGHT = 0.1 #10 cm above the target 

#pick hight to pick from 
PICK_FRACTION= 0.5
PICK_MIN = 0.01
PICK_MAX = 0.04 
GRIPPER_OPEN = 0.06 

#files
GRIPPER_FILE = "data/gripper_down.json" #girpper angles , read oncee from the robot
MARKER_FILE = "data/marker.json" 
DROP_ZONES_FILE = "data/drop_zones.json"
BELT_FILE = "data/belt.json"

#ArUco 
ARUCO_DICT = "DICT_4X4_50" 
TABLE_MARKERS=[0,1,2,3]

#confidence levels
CONFIDENCE_THRESHOLD = 0.5 #as a start
DARK_RATIO_LIMIT = 0.06
IGNORE_NEAR_DROP = 0.07 #if a fruit close this much to a marker conssider as sorted

#conveyor settings
CONVEYOR_SPEED = 30 #percentage of max speed
CONVEYOR_TIMEOUT = 5.0 
SENSOR_PIN ="DI5"
SENSOR_DETECTED ="LOW"
