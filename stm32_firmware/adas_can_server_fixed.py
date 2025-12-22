#!/usr/bin/env python3
"""
CAN Server for ADAS Motor Control - Real-Time Monitor
Enhanced with error recovery and bus monitoring
"""

import can
import socket
import json
import struct
import sys
import time
from datetime import datetime

# Configuration
UDP_IP = "0.0.0.0"
UDP_PORT = 5555
MAX_RETRIES = 3
RETRY_DELAY = 0.1  # seconds

def init_can_bus():
    """Initialize CAN bus with error handling"""
    try:
        bus = can.interface.Bus(channel='can0', interface='socketcan', bitrate=500000)
        print("CAN bus initialized successfully")
        return bus
    except Exception as e:
        print(f"ERROR: Failed to initialize CAN bus: {e}")
        sys.exit(1)

def send_can_message(bus, can_id, data, retries=MAX_RETRIES):
    """Send CAN message with retry logic"""
    for attempt in range(retries):
        try:
            msg = can.Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=False
            )
            bus.send(msg)
            return True
        except can.CanOperationError as e:
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                return False
        except Exception as e:
            return False
    return False

def main():
    """Main CAN server loop"""
    bus = init_can_bus()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    print('='*70)
    print('  CAN Server Started - Real-Time Monitor with Error Recovery')
    print('='*70)
    print(f"  Listening on UDP {UDP_IP}:{UDP_PORT}")
    print(f"  CAN Interface: can0 @ 500kbps")
    print('='*70)
    sys.stdout.flush()
    
    message_count = 0
    error_count = 0
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg_data = json.loads(data.decode('utf-8'))
            
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            message_count += 1
            
            # Extract values
            lane_offset_cm = msg_data.get('lane_offset_cm', 0)
            distance_cm = msg_data.get('distance_cm', 100)
            speed_percent = msg_data.get('speed_percent', 0)
            steering_percent = msg_data.get('steering_percent', 0)
            
            # Pack CAN data
            lane_data = struct.pack('<h', lane_offset_cm)
            dist_data = struct.pack('<H', distance_cm)
            motor_data = struct.pack('<hh', speed_percent, steering_percent)
            
            # Send CAN messages with retries
            success = True
            success &= send_can_message(bus, 0x100, lane_data)
            success &= send_can_message(bus, 0x200, dist_data)
            success &= send_can_message(bus, 0x300, motor_data)
            
            if success:
                # All messages sent successfully
                status = "✓"
            else:
                # Some messages failed
                status = "✗"
                error_count += 1
            
            # Print status
            print(f"{timestamp} {status} Lane:{lane_offset_cm:+4d}cm Dist:{distance_cm:4d}cm "
                  f"Speed:{speed_percent:+3d}% Steer:{steering_percent:+4d}% "
                  f"[{message_count} msgs, {error_count} errors]")
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            print(f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} ERROR: Invalid JSON received")
            sys.stdout.flush()
        except Exception as e:
            print(f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} ERROR: {e}")
            sys.stdout.flush()
            time.sleep(0.5)

if __name__ == "__main__":
    main()
