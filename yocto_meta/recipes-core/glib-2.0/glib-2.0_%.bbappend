# Disable GIO module cache update to prevent build failures
PACKAGE_WRITE_DEPS:remove = "glib-2.0-utils"

# Override intercept to always succeed
do_install:append() {
    # Create a no-op intercept script
    if [ -d ${D}${libdir}/gio/modules ]; then
        rm -f ${D}${libdir}/gio/modules/giomodule.cache
    fi
}
