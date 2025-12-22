/* adas_can.c - SocketCAN implementation for ADAS messages on Raspberry Pi */

#include "adas_can.h"

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>          /* struct ifreq, IFNAMSIZ */
#include <linux/can.h>
#include <linux/can/raw.h>

/* CAN IDs (standard 11-bit) */
#define CAN_ID_LANE_STATUS      0x100
#define CAN_ID_DISTANCE_STATUS  0x200
#define CAN_ID_MOTOR_COMMAND    0x300

int adas_can_open(const char *ifname)
{
    int s;
    struct ifreq ifr;
    struct sockaddr_can addr;

    /* Create CAN RAW socket */
    s = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (s < 0) {
        perror("socket(PF_CAN) failed");
        return -1;
    }

    /* Get interface index by name (e.g. can0) */
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    if (ioctl(s, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl(SIOCGIFINDEX) failed");
        close(s);
        return -1;
    }

    /* Bind the socket to that CAN interface */
    memset(&addr, 0, sizeof(addr));
    addr.can_family  = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;
    if (bind(s, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind(AF_CAN) failed");
        close(s);
        return -1;
    }

    /* Optional: set socket priority for RT behavior (best-effort). */
    int prio = 6; /* range 0..6, higher = more priority. Ignore error. */
    (void)setsockopt(s, SOL_SOCKET, SO_PRIORITY, &prio, sizeof(prio));

    return s;
}

/* Helper: write a single CAN frame, retrying on EINTR */
static int write_frame(int sock, struct can_frame *frame)
{
    ssize_t n;

    do {
        n = write(sock, frame, sizeof(struct can_frame));
    } while (n < 0 && errno == EINTR);

    if (n < 0) {
        perror("write(CAN) failed");
    }
    return (int)n;
}

int adas_send_lane_status(int sock, const lane_data_t *lane)
{
    struct can_frame f;
    memset(&f, 0, sizeof(f));
    f.can_id  = CAN_ID_LANE_STATUS;
    f.can_dlc = 6;

    /* Encode little-endian */
    f.data[0] = (uint8_t)(lane->offset_cm & 0xFF);
    f.data[1] = (uint8_t)((lane->offset_cm >> 8) & 0xFF);
    f.data[2] = (uint8_t)(lane->angle_deg10 & 0xFF);
    f.data[3] = (uint8_t)((lane->angle_deg10 >> 8) & 0xFF);
    f.data[4] = lane->quality;
    f.data[5] = lane->flags;

    return write_frame(sock, &f);
}

int adas_send_distance_status(int sock, const distance_data_t *dist)
{
    struct can_frame f;
    memset(&f, 0, sizeof(f));
    f.can_id  = CAN_ID_DISTANCE_STATUS;
    f.can_dlc = 8;

    f.data[0] = (uint8_t)(dist->dist_front_cm & 0xFF);
    f.data[1] = (uint8_t)((dist->dist_front_cm >> 8) & 0xFF);
    f.data[2] = (uint8_t)(dist->dist_left_cm & 0xFF);
    f.data[3] = (uint8_t)((dist->dist_left_cm >> 8) & 0xFF);
    f.data[4] = (uint8_t)(dist->dist_right_cm & 0xFF);
    f.data[5] = (uint8_t)((dist->dist_right_cm >> 8) & 0xFF);
    f.data[6] = (uint8_t)(dist->rel_speed_cmps & 0xFF);
    f.data[7] = (uint8_t)((dist->rel_speed_cmps >> 8) & 0xFF);

    return write_frame(sock, &f);
}

int adas_send_motor_command(int sock, const motor_command_t *cmd)
{
    struct can_frame f;
    memset(&f, 0, sizeof(f));
    f.can_id  = CAN_ID_MOTOR_COMMAND;
    f.can_dlc = 6;

    f.data[0] = (uint8_t)(cmd->target_speed_cmps & 0xFF);
    f.data[1] = (uint8_t)((cmd->target_speed_cmps >> 8) & 0xFF);
    f.data[2] = (uint8_t)(cmd->steer_angle_deg10 & 0xFF);
    f.data[3] = (uint8_t)((cmd->steer_angle_deg10 >> 8) & 0xFF);
    f.data[4] = cmd->mode;
    f.data[5] = cmd->reserved;

    return write_frame(sock, &f);
}