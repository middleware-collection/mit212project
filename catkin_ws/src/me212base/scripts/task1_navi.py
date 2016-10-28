#!/usr/bin/python

# Task 1 Navigation node: 
import rospy
import tf
import numpy as np
import threading
import serial
import pdb
import traceback
import sys
import tf.transformations as tfm

from me212base.msg import WheelVelCmd
from apriltags.msg import AprilTagDetections
import helper

class ApriltagNavigator():
    def __init__(self, constant_vel = True):
        self.listener = tf.TransformListener()
        self.br = tf.TransformBroadcaster()
        self.apriltag_sub = rospy.Subscriber("/apriltags/detections", AprilTagDetections, self.apriltag_callback, queue_size = 1)
        
        self.velcmd_pub = rospy.Publisher("/cmdvel", WheelVelCmd, queue_size = 1)   ##
        
        if constant_vel:
            self.thread = threading.Thread(target = self.constant_vel_loop)
        else:
            self.thread = threading.Thread(target = self.navi_loop)
            
        self.thread.start()
        
        rospy.sleep(1)
        
    def apriltag_callback(self, data):
        # use apriltag pose detection to find where is the robot
        ##
        for detection in data.detections:
            if detection.id == 0: 
                pose_tag_base = helper.poseTransform(helper.pose2list(detection.pose),  homeFrame = '/camera', targetFrame = '/base_link', listener = self.listener)
                pose_base_map = helper.poseTransform(helper.invPoseList(pose_tag_base), homeFrame = '/apriltag', targetFrame = '/map', listener = self.listener)
                pubFrame(self.br, pose = pose_base_map, frame_id = '/base_link', parent_frame_id = '/map', npub = 1)

    def constant_vel_loop(self):
        while not rospy.is_shutdown() :
            wv = WheelVelCmd()
            self.velcmd_pub.publish(wv) 
            rospy.sleep(0.01) 
        
    def navi_loop(self):
        ##
        target_pose2d = [0.25, 0, np.pi]
        
        ##
        wv = WheelVelCmd()
        
        ## 
        arrived = False
        arrived_position = False
        
        while not rospy.is_shutdown() :
            
            ## 
            # 1. get robot pose
            robot_pose3d = helper.lookupTransformList('/map', '/base_link', self.listener)
            
            if robot_pose3d is None: #rotate in place maybe??
                print '1. Tag not in view, Stop'
                wv.desiredWV_R = 0  # right, left
                wv.desiredWV_L = 0
                self.velcmd_pub.publish(wv)  
                continue
            
            robot_position2d = robot_pose3d[0:2]
            target_position2d = target_pose2d[0:2]
            
            robot_yaw = tfm.euler_from_quaternion(robot_pose3d[3:7]) [2]
            robot_pose2d = robot_position2d + [robot_yaw]
            

            # Call proper function to get obstacles (if there are any) and pose
	    #     - will use kinect to check if obstacle (through distance sensor or rgb corner filter) and generate pose
           
            # 2. navigation policy


            # New navigation policy:
            # 2.1 if not a plan: generate rrt plan
	    #		- path towards the current apriltag
	    # 		- need spline returned, not just waypoints
	    # 2.2 generate wheel velocities
	    #  	        - use inverse kinematics formulas, and velocity and curvature formula on splines
	    # 2.3 grab pose from kalman node and compare with plan
	    # 2.4 Goal test, that is tag-dependent
	    # 		- if satisfied, knock off tag from list

      
            self.velcmd_pub.publish(wv)  
            
            rospy.sleep(0.01)
    
def main():
    rospy.init_node('me212_robot', anonymous=True)
    april_navi = ApriltagNavigator()
    rospy.spin()

if __name__=='__main__':
    main()
    