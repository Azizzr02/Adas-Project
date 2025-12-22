/* can_test.c - Simple ADAS CAN test application */

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>

#include "adas_can.h"

static volatile int g_stop = 0;

static void handle_sigint(int sig)
{
    (void)sig;
    g_stop = 1;
}

static void sleep_ms(unsigned int ms)
{
    struct timespec ts;
    ts.tv_sec  = ms / 1000;
    ts.tv_nsec = (long)(ms % 1000) * 1000000L;
    nanosleep(&ts, NULL);
}

int main(int argc, char *argv[])
{
    const char *ifname = "can0";
    int sock;
    int counter = 0;

    if (argc > 1) {
        ifname = argv[1];  /* allow: ./can-test vcan0 */
    }

    printf("ADAS CAN test starting on interface '%s'\n", ifname);

    signal(SIGINT, handle_sigint);

    sock = adas_can_open(ifname);
    if (sock < 0) {
        fprintf(stderr, "Failed to open CAN interface '%s'\n", ifname);
        return EXIT_FAILURE;
    }

    printf("CAN interface '%s' opened. Press Ctrl+C to stop.\n", ifname);

    while (!g_stop) {
        lane_data_t lane;
        distance_data_t dist;
        motor_command_t cmd;

        /* Example lane data: oscillate offset to simulate small corrections */
        lane.offset_cm   = (int16_t)(10 * (counter % 5) - 20); /* -20, -10, 0, 10, 20 */
        lane.angle_deg10 = (int16_t)(-5 + (counter % 3));      /* -0.5°, -0.4°, -0.3° ... */
        lane.quality     = 90;
        lane.flags       = 0x01;  /* lane detected */

        /* Example distance: object at 12m front, 50m sides */
        dist.dist_front_cm  = 1200;
        dist.dist_left_cm   = 5000;
        dist.dist_right_cm  = 5000;
        dist.rel_speed_cmps = -150;   /* -1.5 m/s relative */

        /* Example motor command: constant speed, small steering oscillation */
        cmd.target_speed_cmps  = 500;  /* 5 m/s */
        cmd.steer_angle_deg10  = (int16_t)(5 * (counter % 7) - 15); /* -1.5° .. +1.5° */
        cmd.mode               = 0x01; /* auto mode */
        cmd.reserved           = 0;

        if (adas_send_lane_status(sock, &lane) > 0) {
            printf("[TX] LANE: offset=%d cm angle=%.1f deg quality=%u flags=0x%02X\n",
                   lane.offset_cm,
                   lane.angle_deg10 / 10.0,
                   lane.quality,
                   lane.flags);
        }

        if (adas_send_distance_status(sock, &dist) > 0) {
            printf("[TX] DIST: front=%u cm left=%u cm right=%u cm rel_speed=%.2f m/s\n",
                   dist.dist_front_cm,
                   dist.dist_left_cm,
                   dist.dist_right_cm,
                   dist.rel_speed_cmps / 100.0);
        }

        if (adas_send_motor_command(sock, &cmd) > 0) {
            printf("[TX] CMD : speed=%.2f m/s steer=%.1f deg mode=0x%02X\n",
                   cmd.target_speed_cmps / 100.0,
                   cmd.steer_angle_deg10 / 10.0,
                   cmd.mode);
        }

        printf("-------------------------------------------------------------\n");
        counter++;
        sleep_ms(500); /* 2 Hz */
    }

    printf("Stopping can-test.\n");
    close(sock);
    return EXIT_SUCCESS;
}
