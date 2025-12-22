#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <net/if.h>

struct can_bittiming {
    unsigned int bitrate;
    unsigned int sample_point;
    unsigned int tq;
    unsigned int prop_seg;
    unsigned int phase_seg1;
    unsigned int phase_seg2;
    unsigned int sjw;
    unsigned int brp;
};

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <bitrate>\n", argv[0]);
        printf("Example: %s 500000\n", argv[0]);
        printf("\nThis will configure can0 with the specified bitrate and bring it UP.\n");
        return 1;
    }

    const char *ifname = "can0";
    unsigned int bitrate = atoi(argv[1]);
    
    if (bitrate == 0) {
        fprintf(stderr, "Invalid bitrate: %s\n", argv[1]);
        return 1;
    }

    int sock = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (sock < 0) {
        perror("socket");
        return 1;
    }

    unsigned int ifindex = if_nametoindex(ifname);
    if (ifindex == 0) {
        perror("if_nametoindex");
        close(sock);
        return 1;
    }

    // First bring interface DOWN
    struct {
        struct nlmsghdr n;
        struct ifinfomsg i;
    } req_down;

    memset(&req_down, 0, sizeof(req_down));
    req_down.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg));
    req_down.n.nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
    req_down.n.nlmsg_type = RTM_NEWLINK;
    req_down.i.ifi_family = AF_UNSPEC;
    req_down.i.ifi_index = ifindex;
    req_down.i.ifi_flags = 0;
    req_down.i.ifi_change = IFF_UP;

    if (send(sock, &req_down, req_down.n.nlmsg_len, 0) < 0) {
        perror("send (down)");
    }

    // Configure bit timing
    struct {
        struct nlmsghdr n;
        struct ifinfomsg i;
        char buf[1024];
    } req;

    memset(&req, 0, sizeof(req));
    req.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg));
    req.n.nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
    req.n.nlmsg_type = RTM_NEWLINK;
    req.i.ifi_family = AF_UNSPEC;
    req.i.ifi_index = ifindex;

    char *p = (char *)&req + NLMSG_ALIGN(req.n.nlmsg_len);
    
    struct rtattr *linkinfo = (struct rtattr *)p;
    linkinfo->rta_type = 18; // IFLA_LINKINFO
    linkinfo->rta_len = RTA_LENGTH(0);
    p += RTA_SPACE(0);
    
    struct rtattr *infodata = (struct rtattr *)p;
    infodata->rta_type = 2; // IFLA_INFO_DATA
    infodata->rta_len = RTA_LENGTH(0);
    p += RTA_SPACE(0);
    
    struct rtattr *bittiming_attr = (struct rtattr *)p;
    bittiming_attr->rta_type = 1; // IFLA_CAN_BITTIMING
    
    struct can_bittiming bt;
    memset(&bt, 0, sizeof(bt));
    bt.bitrate = bitrate;
    
    bittiming_attr->rta_len = RTA_LENGTH(sizeof(bt));
    memcpy(RTA_DATA(bittiming_attr), &bt, sizeof(bt));
    p += RTA_SPACE(sizeof(bt));
    
    infodata->rta_len = p - (char *)infodata;
    linkinfo->rta_len = p - (char *)linkinfo;
    req.n.nlmsg_len = p - (char *)&req;

    if (send(sock, &req, req.n.nlmsg_len, 0) < 0) {
        perror("send (configure)");
        close(sock);
        return 1;
    }

    // Wait for response
    char buf[4096];
    int len = recv(sock, buf, sizeof(buf), 0);
    if (len < 0) {
        perror("recv");
        close(sock);
        return 1;
    }

    // Bring interface UP
    memset(&req_down, 0, sizeof(req_down));
    req_down.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg));
    req_down.n.nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
    req_down.n.nlmsg_type = RTM_NEWLINK;
    req_down.i.ifi_family = AF_UNSPEC;
    req_down.i.ifi_index = ifindex;
    req_down.i.ifi_flags = IFF_UP;
    req_down.i.ifi_change = IFF_UP;

    if (send(sock, &req_down, req_down.n.nlmsg_len, 0) < 0) {
        perror("send (up)");
        close(sock);
        return 1;
    }

    len = recv(sock, buf, sizeof(buf), 0);
    if (len < 0) {
        perror("recv (up)");
        close(sock);
        return 1;
    }

    printf("✓ can0 configured: %u bps and brought UP\n", bitrate);
    close(sock);
    return 0;
}
