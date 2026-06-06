# SMART EVM — Android APK Build Instructions

This app is built with **Kivy + KivyMD** and packaged into an Android APK with **Buildozer**.

---

## Option A — GitHub Actions (easiest, automated)

1. Push this `SmartEVM_Android/` folder to a GitHub repository
2. Go to **Actions** → **Build Android APK** → **Run workflow**
3. Wait ~30 min — the APK will appear under **Artifacts**
4. Download and install it on your Android device

The workflow file is at `.github/workflows/build_apk.yml`.

---

## Option B — Build on your PC (Linux / WSL)

### Prerequisites
- Ubuntu 20.04 or 22.04 (or WSL2 on Windows)
- Python 3.11
- Java 17

### Steps

```bash
# 1. Install system dependencies
sudo apt-get update && sudo apt-get install -y \
  git zip unzip wget lld build-essential \
  libssl-dev libffi-dev python3-dev python3-pip \
  autoconf automake libtool pkg-config

# 2. Install Python build tools
pip install buildozer cython

# 3. Enter the Android app directory
cd SmartEVM_Android

# 4. Build the APK (first build ~30-60 min, downloads Android SDK/NDK)
buildozer android debug

# 5. Find the APK
ls bin/*.apk
```

### Install to Android device
```bash
# via ADB (USB debugging enabled on phone)
adb install bin/smartevm-1.0.0-armeabi-v7a-debug.apk

# Or just copy the APK file to your phone and open it
```

---

## Option C — Google Colab (no local setup needed)

1. Open [Google Colab](https://colab.research.google.com)
2. Create a new notebook and run:

```python
# Install dependencies
!apt-get update && apt-get install -y git zip unzip openjdk-17-jdk
!pip install buildozer cython

# Upload and extract your SmartEVM_Android.zip to Colab
# (Upload the zip via the Files panel)

import zipfile
with zipfile.ZipFile('SmartEVM_Android.zip', 'r') as z:
    z.extractall('.')

# Build APK
import os
os.chdir('SmartEVM_Android')
!buildozer android debug

# Download the APK
from google.colab import files
import glob
apk = glob.glob('bin/*.apk')[0]
files.download(apk)
```

---

## APK Features

- Dashboard with 5 live vote counters, hold-progress bars, lockout countdown, bar chart
- Results — ranked leaderboard showing vote counts and percentages
- Logs — full timestamped event history with vote/error filter
- Settings — edit candidate names, toggle screen orientation (landscape ↔ portrait), clear data
- Export — generates .xlsx Excel report with charts, saved to device storage
- Debug — internal app log viewer

## Connection Setup

1. Flash the ESP8266 firmware from `SMART_EVM.ino`
2. Install this APK on your Android phone
3. Connect your phone to the **SMART_EVM** Wi-Fi hotspot (password: `12345678`)
4. Open the app — it listens on port **8765** for the ESP8266

---

*Made by Ayush Raj, 8C ICSE*
