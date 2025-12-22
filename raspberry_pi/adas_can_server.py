#!/usr/bin/env python3
"""CAN Server - receives messages over UDP and sends to CAN bus using cansend"""
import socket
import struct
import sys
import os

print("✓ CAN server starting (using cansend command)")

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 5555))
print("✓ UDP server listening on port 5555")
print("  Waiting for CAN messages...")
sys.stdout.flush()

msg_count = 0
while True:
    try:
        data, addr = sock.recvfrom(1024)
        
        # Parse: [can_id:4bytes][data:8bytes]
        if len(data) >= 12:
            can_id = struct.unpack('<I', data[:4])[0]
            can_data = data[4:12]
            
            # Use cansend command to send message - format: cansend can0 XXX#YYYYYYYY
            hex_data = can_data.hex().upper()
            cmd = f"/usr/bin/cansend can0 {can_id:03X}#{hex_data}"
            
            # Execute cansend directly without shell
            result = os.system(cmd)
            
            msg_count += 1
            if msg_count % 50 == 0:  # Print every 50th message
                print(f"CAN: 0x{can_id:03X} {hex_data} sent (count: {msg_count}, result: {result})")
                sys.stdout.flush()
    except KeyboardInterrupt:
        print(f"\n✓ Stopped. Total messages: {msg_count}")
        break
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.stdout.flush()
        continue
