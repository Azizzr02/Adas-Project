#!/usr/bin/env python3
"""
Simple CAN test - sends messages to STM32 and verifies green LED toggles
"""

import socket
import json
import time
import sys

def send_can_command(speed_percent=50, steering_percent=0, lane_offset_cm=0, distance_cm=100):
    """Send CAN command via UDP to RPi CAN server"""
    
    # RPi CAN server address
    RPi_IP = "192.168.0.109"
    RPi_PORT = 5555
    
    # Build JSON message
    msg = {
        "speed_percent": int(speed_percent),
        "steering_percent": int(steering_percent),
        "lane_offset_cm": int(lane_offset_cm),
        "distance_cm": int(distance_cm)
    }
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(msg).encode('utf-8'), (RPi_IP, RPi_PORT))
        sock.close()
        return True
    except Exception as e:
        print(f"Error sending: {e}")
        return False

def test_sequence():
    """Send a test sequence of CAN messages"""
    
    print("="*60)
    print("  STM32 CAN Test - Watch GREEN LED")
    print("="*60)
    print(f"Target: RPi 192.168.0.109:5555 -> CAN -> STM32")
    print("")
    
    test_cases = [
        {"name": "Motor on - 25%", "speed": 25, "steering": 0},
        {"name": "Motor on - 50%", "speed": 50, "steering": 0},
        {"name": "Motor on - 75%", "speed": 75, "steering": 0},
        {"name": "Motor off", "speed": 0, "steering": 0},
        {"name": "Lane left", "lane": -50, "speed": 50},
        {"name": "Lane right", "lane": +50, "speed": 50},
        {"name": "Distance near", "distance": 50, "speed": 30},
        {"name": "Distance far", "distance": 200, "speed": 80},
    ]
    
    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"  Sending: Speed={test.get('speed', 0)}%, Steering={test.get('steering', 0)}%, " +
              f"Lane={test.get('lane', 0)}cm, Distance={test.get('distance', 100)}cm")
        
        if send_can_command(
            speed_percent=test.get('speed', 0),
            steering_percent=test.get('steering', 0),
            lane_offset_cm=test.get('lane', 0),
            distance_cm=test.get('distance', 100)
        ):
            print(f"  ✓ Sent successfully - GREEN LED should toggle")
        else:
            print(f"  ✗ Failed to send!")
        
        print("")
        time.sleep(2)
    
    print("="*60)
    print("  Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_sequence()
