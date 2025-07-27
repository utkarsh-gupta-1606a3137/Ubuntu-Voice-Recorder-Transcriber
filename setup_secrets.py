#!/usr/bin/env python3
"""
Setup script to create secrets_config.py from example if missing.
"""
import os
import shutil

example_path = os.path.join(os.path.dirname(__file__), "secrets_config.example.py")
secrets_path = os.path.join(os.path.dirname(__file__), "secrets_config.py")

if not os.path.exists(secrets_path):
    if os.path.exists(example_path):
        shutil.copy(example_path, secrets_path)
        print("Created secrets_config.py from template. Please fill in your sensitive info.")
    else:
        print("Missing secrets_config.example.py template. Please create it manually.")
else:
    print("secrets_config.py already exists.")
