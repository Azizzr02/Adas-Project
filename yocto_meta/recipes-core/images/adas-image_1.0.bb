SUMMARY = "Custom ADAS image for Raspberry Pi"
DESCRIPTION = "Advanced Driver Assistance System image with CAN support"

# Inherit the core minimal image
require recipes-core/images/core-image-minimal.bb

# Configure Raspberry Pi for CAN (MCP2515 on SPI)
RPI_EXTRA_CONFIG:append = " \n\
    dtparam=spi=on \n\
    dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25 \n\
"

# Completely disable man-db to avoid postinstall issues
PACKAGE_EXCLUDE += "man-db man-pages glib-2.0"
BAD_RECOMMENDATIONS += "man-db man-pages glib-2.0 glib-2.0-utils"

# Add our ADAS packages
IMAGE_INSTALL:append = " \
    packagegroup-adas \
    libstdc++ \
"

# Enable additional features (debug-tweaks allows empty root password)
IMAGE_FEATURES += "ssh-server-dropbear debug-tweaks"

# Disable problematic intercepts
do_rootfs[prefuncs] += "disable_gio_intercept"

disable_gio_intercept() {
    # Remove the GIO module cache intercept hook
    if [ -d "${WORKDIR}/intercept_scripts" ]; then
        rm -f ${WORKDIR}/intercept_scripts/postinst_intercept/update_gio_module_cache
    fi
    
    # Also remove from sysroot if present
    if [ -d "${STAGING_DIR_TARGET}/scripts/postinst-intercepts" ]; then
        rm -f ${STAGING_DIR_TARGET}/scripts/postinst-intercepts/update_gio_module_cache
    fi
}

# Kernel modules to autoload
KERNEL_MODULE_AUTOLOAD:append = " can can-raw mcp251x"

# Enable root password login and auto-expand filesystem
ROOTFS_POSTPROCESS_COMMAND:append = " enable_root_login; setup_auto_resize;"

enable_root_login() {
    # Remove -w flag from Dropbear to allow root password login
    if [ -f ${IMAGE_ROOTFS}/etc/default/dropbear ]; then
        sed -i 's/DROPBEAR_EXTRA_ARGS="-w"/DROPBEAR_EXTRA_ARGS=""/' ${IMAGE_ROOTFS}/etc/default/dropbear
    fi
}

setup_auto_resize() {
    # Create init script to expand rootfs on first boot
    cat >> ${IMAGE_ROOTFS}/etc/rc.local << 'EOF'
#!/bin/sh
# Expand root partition on first boot
if [ ! -f /var/lib/rootfs-expanded ]; then
    echo "Expanding root partition..."
    # Expand partition 2 to use all available space
    echo -e "d\n2\nn\np\n2\n278528\n\nw" | fdisk /dev/mmcblk0
    touch /var/lib/rootfs-expanded
    sync
    reboot
fi
EOF
    chmod +x ${IMAGE_ROOTFS}/etc/rc.local
}
