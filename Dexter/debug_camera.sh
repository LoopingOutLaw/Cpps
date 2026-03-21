#!/bin/bash
# Debug script to check camera topics in Gazebo and ROS2
# Run this AFTER launching the simulation

echo "=== Gazebo Topics (gz topic -l) ==="
gz topic -l 2>/dev/null | grep -i "image\|camera" || echo "No Gazebo camera topics found (is simulation running?)"

echo ""
echo "=== ROS2 Topics (ros2 topic list) ==="
source /opt/ros/jazzy/setup.bash
source ~/Cpps/Dexter/install/setup.bash
ros2 topic list 2>/dev/null | grep -i "image\|camera" || echo "No ROS2 camera topics found"

echo ""
echo "=== Check if image_bridge is running ==="
ros2 node list 2>/dev/null | grep -i "image" || echo "No image bridge node found"

echo ""
echo "=== To view camera in Gazebo GUI ==="
echo "In Gazebo, click on the hamburger menu (top right) -> Image Display"
echo "Then select the camera topic to view the feed"
