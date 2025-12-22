#!/bin/sh
# CAN interface setup script
# Sets up can0 with 500kbps bitrate

INTERFACE="can0"
BITRATE="500000"

# Wait for interface to be available
sleep 2

# Check if interface exists
if [ ! -e "/sys/class/net/${INTERFACE}" ]; then
    echo "CAN interface ${INTERFACE} not found"
    exit 1
fi

# Bring interface down
ip link set ${INTERFACE} down 2>/dev/null

# Configure bitrate using netlink (if ip supports it)
ip link set ${INTERFACE} type can bitrate ${BITRATE} 2>/dev/null

# Bring interface up
ip link set ${INTERFACE} up

# Check status
if ip link show ${INTERFACE} | grep -q "UP"; then
    echo "CAN interface ${INTERFACE} configured successfully at ${BITRATE} bps"
    exit 0
else
    echo "Failed to bring up ${INTERFACE}"
    exit 1
fi
