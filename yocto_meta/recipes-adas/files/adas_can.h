/* adas_can.h - Simple ADAS CAN abstraction for Raspberry Pi (SocketCAN) */
#ifndef ADAS_CAN_H
#define ADAS_CAN_H

#include <stdint.h>

/* ===== ADAS data types ===== */

/* Lane data: lane keeping / lane detection */
typedef struct {
    int16_t offset_cm;      /* lateral offset from lane center in cm (+right, -left) */
    int16_t angle_deg10;    /* lane angle in 0.1 deg (e.g. -35 = -3.5°) */
    uint8_t quality;        /* 0..100% confidence */
    uint8_t flags;          /* bit0: lane_detected, others reserved */
} lane_data_t;

/* Distance data: front/left/right obstacle distances */
typedef struct {
    uint16_t dist_front_cm;  /* 0..65535, 0xFFFF = no object */
    uint16_t dist_left_cm;
    uint16_t dist_right_cm;
    int16_t  rel_speed_cmps; /* relative speed in cm/s (signed) */
} distance_data_t;

/* Motor command: speed + steering command */
typedef struct {
    int16_t target_speed_cmps;   /* signed, cm/s (negative = reverse) */
    int16_t steer_angle_deg10;   /* 0.1 deg steering angle */
    uint8_t mode;                /* bit0: auto, bit1: emergency, others reserved */
    uint8_t reserved;
} motor_command_t;

/* ===== API ===== */

/* Open a CAN RAW socket on interface (e.g. "can0").
 * Returns socket fd >= 0 on success, -1 on error.
 */
int adas_can_open(const char *ifname);

/* Send lane status frame (CAN ID 0x100). Returns bytes written or -1. */
int adas_send_lane_status(int sock, const lane_data_t *lane);

/* Send distance status frame (CAN ID 0x200). Returns bytes written or -1. */
int adas_send_distance_status(int sock, const distance_data_t *dist);

/* Send motor command frame (CAN ID 0x300). Returns bytes written or -1. */
int adas_send_motor_command(int sock, const motor_command_t *cmd);

#endif /* ADAS_CAN_H */