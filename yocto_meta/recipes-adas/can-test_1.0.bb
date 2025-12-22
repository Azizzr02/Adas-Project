SUMMARY = "ADAS CAN Test Application"
DESCRIPTION = "Test application for ADAS CAN communication"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

# All source files are in the 'files' directory
SRC_URI = "file://adas_can.c \
           file://adas_can.h \
           file://can_test.c \
           file://Makefile"

S = "${WORKDIR}"

# Use the Makefile to build
do_compile() {
    oe_runmake
}

do_install() {
    install -d ${D}${bindir}
    install -m 0755 can-test ${D}${bindir}
}

FILES:${PN} = "${bindir}/can-test"