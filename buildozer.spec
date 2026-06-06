[app]

title = SMART EVM
package.name = smartevm
package.domain = org.smartevm

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,websockets,openpyxl,pillow

orientation = landscape

fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

android.archs = arm64-v8a

android.allow_backup = True

android.logcat_filters = *:S python:D

# Pin python-for-android to a version that uses Python 3.11 (not 3.14)
p4a.branch = v2023.09.16

[buildozer]
log_level = 2
warn_on_root = 1
