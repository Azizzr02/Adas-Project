#!/bin/sh
### BEGIN INIT INFO
# Provides:          can-init
# Required-Start:    $local_fs $network
# Required-Stop:     $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Configure CAN interface at boot
### END INIT INFO

INTERFACE="can0"
BITRATE="500000"

case "$1" in
    start)
        echo "Configuring CAN interface ${INTERFACE}..."
        
        # Wait for interface
        timeout=10
        while [ $timeout -gt 0 ] && [ ! -e "/sys/class/net/${INTERFACE}" ]; do
            sleep 1
            timeout=$((timeout - 1))
        done
        
        if [ ! -e "/sys/class/net/${INTERFACE}" ]; then
            echo "ERROR: ${INTERFACE} not found"
            exit 1
        fi
        
        # Configure CAN
        if [ -x /usr/sbin/ip ]; then
            /usr/sbin/ip link set ${INTERFACE} type can bitrate ${BITRATE}
            /usr/sbin/ip link set ${INTERFACE} up
            echo "CAN ${INTERFACE} UP at ${BITRATE} bps"
        fi
        ;;
    stop)
        ip link set ${INTERFACE} down 2>/dev/null || true
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
