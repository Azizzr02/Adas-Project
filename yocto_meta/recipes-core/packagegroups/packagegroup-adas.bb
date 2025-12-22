SUMMARY = "ADAS package group"
DESCRIPTION = "Package group for Advanced Driver Assistance System"
LICENSE = "MIT"

inherit packagegroup

RDEPENDS:${PN} = " \
    adas-app \
    can-utils \
    can-setup \
    iproute2 \
    kernel-modules \
    python3-core \
    python3-io \
    python3-netclient \
    python3-threading \
    python3-logging \
    python3-json \
    e2fsprogs \
    e2fsprogs-resize2fs \
"


