#!/bin/bash
# CAN Interface Reset and Test Script for Raspberry Pi
# Usage: ./can_reset.sh [send|test]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== CAN Interface Reset ===${NC}"

# Bring interface down
echo "Bringing CAN interface down..."
ip link set can0 down 2>/dev/null || true
sleep 1

# Remove driver
echo "Removing mcp251x driver..."
rmmod mcp251x 2>/dev/null || true
sleep 2

# Reload driver
echo "Loading mcp251x driver..."
modprobe mcp251x
sleep 3

# Configure and bring up
echo "Configuring CAN interface..."
ip link set can0 type can bitrate 500000 restart-ms 100
ip link set can0 up
sleep 2

# Show status
echo ""
echo -e "${GREEN}CAN Interface Status:${NC}"
ip -d link show can0 | grep -E "can state|bitrate"

if [ "$1" == "send" ]; then
    echo ""
    echo -e "${YELLOW}=== Sending Test Messages ===${NC}"
    echo "Watch the STM32 GREEN LED - should toggle on EACH message!"
    echo ""
    
    i=1
    while [ $i -le 10 ]; do
        echo "Message $i..."
        cansend can0 300#0A00
        sleep 1
        i=$((i+1))
    done
    
    echo ""
    echo -e "${GREEN}Statistics:${NC}"
    ip -s link show can0
    
elif [ "$1" == "test" ]; then
    echo ""
    echo -e "${YELLOW}=== Testing Single Message ===${NC}"
    echo "Sending one message..."
    cansend can0 123#DEADBEEF
    sleep 1
    
    echo -e "${GREEN}Statistics:${NC}"
    ip -s link show can0
else
    echo ""
    echo -e "${YELLOW}Interface ready for commands:${NC}"
    echo "  cansend can0 300#0A00          - Send a single message"
    echo "  candump can0                   - Monitor incoming messages"
    echo "  ip -s link show can0           - Show statistics"
fi
