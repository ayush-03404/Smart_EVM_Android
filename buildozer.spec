[app]

title = SMART EVM
package.name = smartevm
package.domain = org.smartevm

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,websockets,openpyxl,pillow,et_xmlfile

orientation = landscape

fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

android.arch = arm64-v8a

android.allow_backup = True

# App icon (uses default kivy icon if not present)
# icon.filename = %(source.dir)s/icon.png

# Presplash
# presplash.filename = %(source.dir)s/presplash.png

android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
