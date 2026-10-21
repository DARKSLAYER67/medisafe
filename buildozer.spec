[app]

# (str) Title of your application
title = MediSafe

# (str) Package name
package.name = medisafe

# (str) Package domain (needed for android packaging)
package.domain = org.medisafe

# (list) Source files to include (let it include python files, assets, etc.)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
# Specify dependencies clearly so Buildozer bundles them into the APK
requirements = python3,kivy,gtts,requests,urllib3,certifi,idna,charset-normalizer

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (list) Supported languages
# android.locales = en,hi

[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1