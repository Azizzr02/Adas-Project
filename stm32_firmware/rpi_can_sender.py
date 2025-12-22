#!/usr/bin/env python3
"""
CAN Message Sender for Raspberry Pi to STM32 Communication
This script sends motor control commands via CAN bus to the STM32 ADAS motor controller
"""

import can
import time
import sys

# CAN Configuration
CAN_INTERFACE = 'can0'  # Change to your CAN interface name
CAN_BITRATE = 500000    # 500 kbps (must match STM32 configuration)

# CAN Message IDs (matching STM32 protocol)
CAN_ID_LANE = 0x100        # Lane offset command
CAN_ID_DISTANCE = 0x200    # Distance to vehicle ahead
CAN_ID_MOTOR = 0x300       # Motor speed command

def setup_can_interface():
    """Initialize CAN interface"""
    try:
        bus = can.interface.Bus(channel=CAN_INTERFACE, bustype='socketcan')
        print(f"CAN interface {CAN_INTERFACE} initialized successfully")
        return bus
    except Exception as e:
        print(f"Error initializing CAN interface: {e}")
        print("Make sure to run: sudo ip link set can0 type can bitrate 500000 && sudo ip link set can0 up")
        sys.exit(1)

def send_motor_speed(bus, speed_percent):
    """
    Send motor speed command to STM32
    
    Args:
        bus: CAN bus object
        speed_percent: Motor speed (0-85%, limited for safety)
    """
    if speed_percent < 0 or speed_percent > 85:
        print("Speed must be between 0 and 85 (safety limit)")
        return False
    
    # Pack as int16 little-endian
    speed_int16 = int(speed_percent)
    data = [
        speed_int16 & 0xFF,         # Low byte
        (speed_int16 >> 8) & 0xFF   # High byte
    ]
    
    msg = can.Message(
        arbitration_id=CAN_ID_MOTOR,
        data=data,
        is_extended_id=False
    )
    
    try:
        bus.send(msg)
        print(f"Sent motor speed: {speed_percent}%")
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def send_motor_direction(bus, direction):
    """
    Send lane offset to STM32 (for future steering control)
    
    Args:
        bus: CAN bus object
        direction: Lane offset in cm (-100 to +100, negative=left, positive=right)
    """
    if direction < -100 or direction > 100:
        print("Lane offset must be between -100 and +100 cm")
        return False
    
    # Pack as int16 little-endian
    offset_int16 = int(direction)
    if offset_int16 < 0:
        offset_int16 = offset_int16 & 0xFFFF  # Two's complement for negative
    
    data = [
        offset_int16 & 0xFF,         # Low byte
        (offset_int16 >> 8) & 0xFF   # High byte
    ]
    
    msg = can.Message(
        arbitration_id=CAN_ID_LANE,
        data=data,
        is_extended_id=False
    )
    
    try:
        bus.send(msg)
        print(f"Sent lane offset: {direction} cm")
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def send_distance(bus, distance_cm):
    """
    Send distance to vehicle ahead to STM32
    
    Args:
        bus: CAN bus object
        distance_cm: Distance in centimeters (0-65535)
    """
    if distance_cm < 0 or distance_cm > 65535:
        print("Distance must be between 0 and 65535 cm")
        return False
    
    # Pack as uint16 little-endian
    distance_uint16 = int(distance_cm)
    data = [
        distance_uint16 & 0xFF,         # Low byte
        (distance_uint16 >> 8) & 0xFF   # High byte
    ]
    
    msg = can.Message(
        arbitration_id=CAN_ID_DISTANCE,
        data=data,
        is_extended_id=False
    )
    
    try:
        bus.send(msg)
        print(f"Sent distance: {distance_cm} cm")
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def send_motor_stop(bus):
    """Send motor stop command to STM32 (speed = 0)"""
    return send_motor_speed(bus, 0)

def demo_sequence(bus):
    """Run a demonstration sequence of motor commands"""
    print("\n=== Running Demo Sequence ===")
    print("WARNING: Make sure propeller is removed for safety!")
    print("Press Ctrl+C within 5 seconds to abort...")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nDemo aborted by user")
        return
    
    # Start at 0% speed
    print("\n1. Starting motor at 0% (idle)")
    send_motor_speed(bus, 0)
    time.sleep(2)
    
    # Gradually increase to 20%
    print("\n2. Increasing to 20% speed")
    for speed in range(0, 21, 5):
        send_motor_speed(bus, speed)
        time.sleep(0.5)
    time.sleep(2)
    
    # Increase to 40%
    print("\n3. Increasing to 40% speed")
    for speed in range(25, 41, 5):
        send_motor_speed(bus, speed)
        time.sleep(0.5)
    time.sleep(3)
    
    # Test distance reporting
    print("\n4. Sending distance updates (simulated)")
    send_distance(bus, 500)  # 5 meters
    time.sleep(0.5)
    send_distance(bus, 300)  # 3 meters
    time.sleep(0.5)
    send_distance(bus, 150)  # 1.5 meters
    time.sleep(1)
    
    # Test lane offset
    print("\n5. Sending lane offset (simulated)")
    send_motor_direction(bus, -10)  # 10cm left
    time.sleep(0.5)
    send_motor_direction(bus, 15)   # 15cm right
    time.sleep(0.5)
    send_motor_direction(bus, 0)    # Centered
    time.sleep(1)
    
    # Reduce speed
    print("\n6. Reducing to 20% speed")
    for speed in range(40, 19, -5):
        send_motor_speed(bus, speed)
        time.sleep(0.5)
    time.sleep(2)
    
    # Stop motor
    print("\n7. Stopping motor")
    send_motor_stop(bus)
    
    print("\n=== Demo Complete ===\n")

def interactive_mode(bus):
    """Interactive mode for manual control"""
    print("\n=== Interactive ADAS Motor Control ===")
    print("Commands:")
    print("  s <0-85>      - Set motor speed (0-85%, safety limited)")
    print("  l <-100-100>  - Set lane offset in cm (negative=left, positive=right)")
    print("  d <0-65535>   - Set distance in cm")
    print("  stop          - Stop motor (speed = 0)")
    print("  quit          - Exit program")
    print("=========================================\n")
    print("WARNING: ESC must be armed before motor responds!")
    print("Remove propeller for initial testing!\n")
    
    while True:
        try:
            cmd = input("Enter command: ").strip().lower()
            
            if cmd == 'quit' or cmd == 'exit':
                break
            elif cmd == 'stop':
                send_motor_stop(bus)
            elif cmd.startswith('s '):
                try:
                    speed = int(cmd.split()[1])
                    send_motor_speed(bus, speed)
                except (IndexError, ValueError):
                    print("Invalid speed value. Use: s <0-85>")
            elif cmd.startswith('l '):
                try:
                    offset = int(cmd.split()[1])
                    send_motor_direction(bus, offset)
                except (IndexError, ValueError):
                    print("Invalid lane offset. Use: l <-100-100>")
            elif cmd.startswith('d '):
                try:
                    distance = int(cmd.split()[1])
                    send_distance(bus, distance)
                except (IndexError, ValueError):
                    print("Invalid distance. Use: d <0-65535>")
            else:
                print("Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break

def main():
    """Main function"""
    print("=== Raspberry Pi to STM32 CAN Sender ===\n")
    
    # Initialize CAN bus
    bus = setup_can_interface()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        demo_sequence(bus)
    else:
        interactive_mode(bus)
    
    # Close CAN bus
    bus.shutdown()
    print("CAN bus closed. Goodbye!")

if __name__ == "__main__":
    main()
