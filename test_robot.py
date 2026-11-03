# !/usr/bin/env python3
"""Basic test of the Niryo Ned2 robot with pyniryo.

Usage:
    pip install pyniryo
    python test_robot.py

Before running:
- PC on the same network as the robot (or connected by Ethernet cable).
- Area around the arm clear.
- Hand near the robot's power switch.
"""
from pyniryo import NiryoRobot

ROBOT_IP = "10.10.10.10"
TEST_GRIPPER = False   # set to True if the gripper is connected and recognized
DELTA_RAD = 0.15       # small movement on the base joint (~9 degrees)
SPEED = 30             # % of maximum speed


def to_list(joints):
    """Convert the return value of get_joints() to a list, whatever the version."""
    return joints.to_list() if hasattr(joints, "to_list") else list(joints)


print(f"Connecting to {ROBOT_IP}...")
robot = NiryoRobot(ROBOT_IP)

try:
    print("Connection OK.")

    # 1. Calibration (only if needed)
    if robot.need_calibration():
        print("Robot needs calibration. Calibrating (the arm will move)...")
        robot.calibrate_auto()
    else:
        print("Robot already calibrated.")

    robot.set_learning_mode(False)
    robot.set_arm_max_velocity(SPEED)

    # 2. State reading
    joints = to_list(robot.get_joints())
    print("Joints (rad):", [round(j, 3) for j in joints])
    print("Pose (x, y, z, roll, pitch, yaw):", robot.get_pose())

    # 3. Small movement on joint 1 and back
    target = list(joints)
    target[0] += DELTA_RAD
    print("Moving the base...")
    robot.move_joints(target)
    print("Returning to the initial position...")
    robot.move_joints(joints)

    # 4. Gripper (optional)
    if TEST_GRIPPER:
        robot.update_tool()
        print("Opening the gripper...")
        robot.open_gripper()
        print("Closing the gripper...")
        robot.close_gripper()

    print("Test completed without errors.")

finally:
    robot.close_connection()
    print("Connection closed.")
