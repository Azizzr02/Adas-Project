# This class disables the problematic man-db intercept hook

PACKAGE_EXCLUDE += "man-db man-pages"

python __anonymous() {
    # Remove man-db intercept hook
    import os
    staging_dir = d.getVar('STAGING_DIR_NATIVE')
    intercept = os.path.join(staging_dir, 'usr/share/postinst-intercepts/update_mandb')
    if os.path.exists(intercept):
        os.remove(intercept)
}
