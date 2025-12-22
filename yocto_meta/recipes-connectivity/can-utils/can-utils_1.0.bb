DESCRIPTION = "can-utils from linux-can (upstream master)"
SECTION = "console/utils"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://LICENSES/GPL-2.0-only.txt;md5=f9d20a453221a1b7e32ae84694da2c37"

SRC_URI = "file://can-utils-master.tar.gz"
SRC_URI[sha256sum] = "536e6606e9aeb77f9fbdfd4925d106a19fd97397f9c7f36b60817d7c9b00f5c2"

S = "${WORKDIR}/can-utils-master"

inherit gettext

do_compile() {
    oe_runmake
}

do_install() {
    oe_runmake DESTDIR=${D} PREFIX=${prefix} install || true
}

FILES_${PN} += "${bindir}/*"

DESCRIPTION = "Utilities for using CAN sockets"