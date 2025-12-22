SUMMARY = "Minimal ADAS image without man-db issues"
DESCRIPTION = "Simplified ADAS image based directly on core-image-minimal"

require recipes-core/images/core-image-minimal.bb

inherit extrausers

# Completely exclude man-db
IMAGE_INSTALL:remove = "man-db man-pages"
PACKAGE_EXCLUDE += "man-db man-pages"

# Add our packages
IMAGE_INSTALL:append = " \
    can-utils \
    can-setup \
    iproute2 \
    kernel-module-can \
    kernel-module-can-raw \
    kernel-module-mcp251x \
"

IMAGE_FEATURES += "ssh-server-dropbear"

# Simple root password
EXTRA_USERS_PARAMS = "usermod -P root root;"

# Auto-load CAN modules
KERNEL_MODULE_AUTOLOAD:append = " can can-raw mcp251x"

# Remove the problematic man-db intercept hook
ROOTFS_POSTPROCESS_COMMAND += "remove_mandb_intercept;"

remove_mandb_intercept() {
    # Remove intercept hooks that would fail without man-db
    rm -f ${IMAGE_ROOTFS}/usr/share/postinst-intercepts/update_mandb
    rm -f ${IMAGE_ROOTFS}/var/lib/rpm/Packages
    rm -rf ${IMAGE_ROOTFS}/var/cache/man
    
    # Also clean up any pending postinstall scripts related to mandb
    find ${IMAGE_ROOTFS}/etc/rpm-postinsts/ -name "*man-db*" -delete 2>/dev/null || true
    
    bbwarn "Removed man-db intercept hooks"
}
