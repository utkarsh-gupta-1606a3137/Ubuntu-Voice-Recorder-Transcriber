#!/usr/bin/env python3
"""
Generate VoiceRecorder.desktop file from app_config.py
"""
import os
from secrets_config import MAIN_SCRIPT_PATH, ICON_PATH

desktop_entry = f"""[Desktop Entry]
Version=1.0
Name=Voice Recorder
Comment=Record audio and transcribe it
Exec=python3 {MAIN_SCRIPT_PATH}
Icon={ICON_PATH}
Terminal=false
Type=Application
Categories=Audio;Utility;
StartupNotify=true
"""

desktop_path = os.path.join(os.path.dirname(__file__), "VoiceRecorder.desktop")
with open(desktop_path, "w") as f:
    f.write(desktop_entry)
print(f"VoiceRecorder.desktop generated at {desktop_path}")
