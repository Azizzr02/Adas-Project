SUMMARY = "CAN interface setup utility"
DESCRIPTION = "Simple utility to configure CAN bitrate via netlink"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://can-setup.c \
           file://can-init.sh \
          "

S = "${WORKDIR}"

inherit update-rc.d

INITSCRIPT_NAME = "can-init"
INITSCRIPT_PARAMS = "defaults 99"

do_compile() {
    ${CC} ${CFLAGS} ${LDFLAGS} can-setup.c -o can-setup
}

do_install() {
    install -d ${D}${bindir}
    install -m 0755 can-setup ${D}${bindir}/can-setup
    
    install -d ${D}${sysconfdir}/init.d
    install -m 0755 ${WORKDIR}/can-init.sh ${D}${sysconfdir}/init.d/can-init
}
