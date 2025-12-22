#!/usr/bin/env python3
"""Send CAN messages from RPi to STM32"""

import socket
import struct
import time
import sys

def send_can_messages(count=10, delay=1):
    """Send CAN messages"""
    try:
        # Setup CAN socket
        can_socket = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        can_socket.bind(('can0',))
        
        print("=== Sending CAN Messages ===")
        print(f"Sending {count} messages with {delay}s delay")
        print("Watch GREEN LED on STM32 - should toggle on EACH message")
        print("")
        
        for i in range(1, count + 1):
            # CAN frame with ID 0x300, data 0x0A 0x00
            can_id = 0x300
            data = bytes([0x0A, 0x00])
            dlc = len(data)
            
            # Pack into CAN frame structure
            frame = struct.pack('=IB3s8s', 
                               can_id,                              # CAN ID
                               dlc,                                 # DLC
                               b'\x00\x00\x00',                    # Padding/flags
                               data + b'\x00' * (8 - len(data)))   # Data + padding
            
            can_socket.send(frame)
            print(f"Message {i:2d} sent (ID: 0x{can_id:03X}, DLC: {dlc}, Data: {data.hex().upper()})")
            
            time.sleep(delay)
        
        can_socket.close()
        print("")
        print("=== All messages sent ===")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    send_can_messages()
