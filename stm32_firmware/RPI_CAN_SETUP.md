# Raspberry Pi CAN Setup for STM32 Communication

## Hardware Connection
1. Connect CAN transceiver (e.g., MCP2515 or SN65HVD230) to Raspberry Pi
2. Connect CAN_H and CAN_L between Raspberry Pi and STM32
3. Ensure common ground between devices
4. Add 120Ω termination resistors at both ends of the CAN bus

## Software Setup on Raspberry Pi

### 1. Enable CAN Interface
```bash
# Load CAN modules
sudo modprobe can
sudo modprobe can_raw

# Configure CAN interface (500 kbps to match STM32)
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up

# Verify interface is up
ip -details link show can0
```

### 2. Install Python CAN Library
```bash
sudo apt-get update
sudo apt-get install python3-pip
pip3 install python-can
```

### 3. Make CAN Interface Persistent (Optional)
Edit `/etc/network/interfaces`:
```
auto can0
iface can0 inet manual
    pre-up /sbin/ip link set can0 type can bitrate 500000
    up /sbin/ifconfig can0 up
    down /sbin/ifconfig can0 down
```

## Usage

### Run Demo Sequence
```bash
python3 rpi_can_sender.py demo
```

### Interactive Mode
```bash
python3 rpi_can_sender.py
```

Then use commands:
- `s 50` - Set motor speed to 50%
- `s 0` - Stop motor
- `l -10` - Set lane offset 10cm left
- `l 15` - Set lane offset 15cm right
- `d 500` - Set distance to 500cm (5 meters)
- `stop` - Stop motor
- `quit` - Exit

## Testing CAN Communication

### Send test message manually
```bash
# Send motor speed command (20% = 0x0014 in little-endian)
cansend can0 300#1400

# Send distance (500cm = 0x01F4 in little-endian)
cansend can0 200#F401

# Send lane offset (-10cm = 0xFFF6 in little-endian, two's complement)
cansend can0 100#F6FF
```

### Monitor CAN traffic
```bash
candump can0
```

### Check CAN statistics
```bash
ip -s -d link show can0
```

## CAN Message Protocol

### Message IDs:
- `0x100` (CAN_ID_LANE) - Lane Offset
  - Data[0]: Offset low byte
  - Data[1]: Offset high byte
  - Format: int16 (signed, -100 to +100 cm)
  - Negative = left offset, Positive = right offset

- `0x200` (CAN_ID_DISTANCE) - Distance to Vehicle Ahead
  - Data[0]: Distance low byte
  - Data[1]: Distance high byte
  - Format: uint16 (unsigned, 0-65535 cm)

- `0x300` (CAN_ID_MOTOR) - Motor Speed Command
  - Data[0]: Speed low byte
  - Data[1]: Speed high byte
  - Format: int16 (0-85%, limited for safety)
  - ESC generates 50Hz PWM: 1ms (0%) to 2ms (100%)

### Notes:
- All multi-byte values use **little-endian** format (LSB first)
- Motor uses A2212 Brushless with XXD 40A ESC
- ESC must be armed before motor responds (done automatically on STM32 boot)
- Speed is limited to 85% for safety
- PWM on TIM4 Channel 1, frequency = 50Hz (standard for ESCs)

## Troubleshooting

### CAN interface won't come up
```bash
# Check kernel modules
lsmod | grep can

# Check dmesg for errors
dmesg | grep can
```

### No communication with STM32
1. Verify CAN bitrate matches on both sides (500 kbps)
2. Check physical connections (CAN_H, CAN_L, GND)
3. Verify termination resistors are present
4. Use oscilloscope to verify CAN signals
5. Check STM32 CAN pins: PB8 (RX), PB9 (TX)

### Permission denied on /dev/can0
```bash
sudo chmod 666 /dev/can0
# Or run script with sudo
sudo python3 rpi_can_sender.py
```
