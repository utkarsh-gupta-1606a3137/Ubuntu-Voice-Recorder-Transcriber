#!/usr/bin/env python3
"""
Ubuntu Voice Recording Application
Main entry point for the application
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from voice_recorder_app import VoiceRecorderApp

def main():
    """Main entry point"""
    app = VoiceRecorderApp()
    app.run()

if __name__ == "__main__":
    main()
