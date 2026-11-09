[app]

# Title of the application
title = DCIM Calibration

# Package name (reverse domain style, required for Android)
package.name = dcimcalibration

# Package domain (needed for android.package)
package.domain = org.bigfguy8

# Source directory
source.dir = .

# Source code entry point
source.main = main.py

# Source files to include
source.include_exts = py,png,jpg,kv,atlas

# Version
version = 1.0.0

# Requirements (python3 + kivy for the Kivy app)
requirements = python3,kivy

# Supported orientations
orientation = portrait

# Android API target (stable API target per instructions)
android.api = 33

# Minimum Android API the app supports
android.minapi = 24

# Android NDK version to use (r27c is a valid, downloadable release)
android.ndk = 27c

# Architecture: arm64-v8a only (ARM64 PRoot, avoid x86_64)
arch = arm64-v8a

# Whether to enable signature
android.signing = false

# Accept Android SDK license automatically (avoids interactive prompt)
android.accept_sdk_license = True

# Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA

# Entry point activity
android.entrypoint = org.kivy.android.PythonActivity

# Meta-data
android.meta_data =

# Android extensions / arguments
android.add_jar =
android.add_aar =
android.add_so_lib =
android.add_activity =
android.add_service =
android.add_receiver =
android.add_provider =
android.add_manifest_uses =

# Buildozer runtime settings
log_level = 2
warn_on_root = 1
build_dir = .buildozer
bin_dir = bin
thread_count = 2

[android.webview]

# User agent string
android.webview.useragent = Mozilla/5.0 (Linux; Android 13; ...) AppleWebKit/537.36

# Cache size
android.webview.cache_size = 0

[iOS]

# No iOS settings needed for an Android-only build
