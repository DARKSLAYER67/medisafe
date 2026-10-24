[app]

# (str) Title of your application
title = MediSafe

# (str) Package name
package.name = medisafe

# (str) Package domain (needed for android packaging)
package.domain = org.medisafe

# (str) Where are the source files located? (.) means current directory
source.dir = .

# (list) Source files to include (let it include python files, assets, etc.)
source.include_exts = py,png,jpg,kv,atlas,mp3

# (str) Application version (Required by Buildozer)
version = 1.0

# (list) Application requirements
requirements = python3,kivy,gtts,requests,urllib3,certifi,idna,charset-normalizer

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE,WAKE_LOCK

# Android target configuration for APK builds
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.arch = arm64-v8a
android.accept_sdk_license = True

# Build and packaging settings
p4a.branch = develop
[buildozer]
# (int) Log level (0 = error, 1 = info, 2 = debug)
log_level = 2
warn_on_root = 1
