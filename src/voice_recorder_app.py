#!/usr/bin/env python3
"""
Voice Recorder GTK Application
Main GUI application for voice recording and transcription
"""


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import threading
import pyperclip
import os
import shutil

# Auto-create secrets_config.py if missing
secrets_path = os.path.join(os.path.dirname(__file__), "../secrets_config.py")
example_path = os.path.join(os.path.dirname(__file__), "../secrets_config.example.py")
if not os.path.exists(secrets_path):
    if os.path.exists(example_path):
        shutil.copy(example_path, secrets_path)
        print("Created secrets_config.py from template. Please fill in your sensitive info.")
    else:
        print("Missing secrets_config.example.py template. Please create it manually.")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from secrets_config import OPENAI_API_KEY, MAIN_SCRIPT_PATH, ICON_PATH
from audio_recorder import AudioRecorder
from transcription_service import TranscriptionService
from file_manager import FileManager

class VoiceRecorderApp:
    """Main GTK application for voice recording"""

    def __init__(self):
        """Initialize the application"""
        self.audio_recorder = AudioRecorder()
        self.transcription_service = TranscriptionService()
        self.file_manager = FileManager()

        # Application state
        self.is_recording = False
        self.current_recording_path = None

        # Create the UI
        self._create_ui()

        # Set up audio level callback
        self.audio_recorder.on_level(self._on_audio_level)

    def _create_ui(self):
        """Create the main UI"""
        # Main window
        self.window = Gtk.Window()
        self.window.set_title("Voice Recorder")
        self.window.set_default_size(500, 400)

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.window.add(main_box)

        # Settings button
        settings_button = Gtk.Button(label="Settings")
        settings_button.set_halign(Gtk.Align.END)
        settings_button.connect("clicked", self._on_settings_clicked)
        main_box.pack_start(settings_button, False, False, 0)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b><big>Voice Recorder &amp; Transcription</big></b>")
        title_label.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(title_label, False, False, 0)

        # Status section
        status_frame = Gtk.Frame(label="Status")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        status_box.set_margin_left(10)
        status_box.set_margin_right(10)
        status_box.set_margin_top(10)
        status_box.set_margin_bottom(10)
        status_frame.add(status_box)

        self.status_label = Gtk.Label("Ready to record")
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, False, False, 0)

        # Audio level indicator
        level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        level_box.pack_start(Gtk.Label("Audio Level:"), False, False, 0)

        self.level_bar = Gtk.ProgressBar()
        self.level_bar.set_show_text(True)
        self.level_bar.set_text("Silent")
        level_box.pack_start(self.level_bar, True, True, 0)

        status_box.pack_start(level_box, False, False, 0)
        main_box.pack_start(status_frame, False, False, 0)

        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)

        self.start_button = Gtk.Button(label="Start Recording")
        self.start_button.connect("clicked", self._on_start_recording)
        self.start_button.set_size_request(150, 40)
        button_box.pack_start(self.start_button, False, False, 0)

        self.stop_button = Gtk.Button(label="Stop Recording")
        self.stop_button.connect("clicked", self._on_stop_recording)
        self.stop_button.set_sensitive(False)
        self.stop_button.set_size_request(150, 40)
        button_box.pack_start(self.stop_button, False, False, 0)

        main_box.pack_start(button_box, False, False, 0)

        # Transcription section
        transcript_frame = Gtk.Frame(label="Transcription")
        transcript_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        transcript_box.set_margin_left(10)
        transcript_box.set_margin_right(10)
        transcript_box.set_margin_top(10)
        transcript_box.set_margin_bottom(10)
        transcript_frame.add(transcript_box)

        # Transcription text area with scrolling
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(150)

        self.transcript_buffer = Gtk.TextBuffer()
        self.transcript_view = Gtk.TextView(buffer=self.transcript_buffer)
        self.transcript_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.transcript_view.set_editable(False)
        scrolled_window.add(self.transcript_view)

        transcript_box.pack_start(scrolled_window, True, True, 0)

        # Copy button
        copy_button = Gtk.Button(label="Copy to Clipboard")
        copy_button.connect("clicked", self._on_copy_transcript)
        copy_button.set_halign(Gtk.Align.CENTER)
        transcript_box.pack_start(copy_button, False, False, 0)

        # Add play button for current recording
        play_button = Gtk.Button(label="Play Current Recording")
        play_button.connect("clicked", self._on_play_recording)
        play_button.set_halign(Gtk.Align.CENTER)
        transcript_box.pack_start(play_button, False, False, 0)

        # Add import button for audio files
        import_button = Gtk.Button(label="Import Audio File")
        import_button.connect("clicked", self._on_import_audio)
        import_button.set_halign(Gtk.Align.CENTER)
        transcript_box.pack_start(import_button, False, False, 0)

        main_box.pack_start(transcript_frame, True, True, 0)

        # Check service availability
        self._update_ui_state()
    def _on_settings_clicked(self, button):
        """Open the settings dialog"""
        from app_config import RECORDINGS_DIR
        dialog = Gtk.Dialog(title="Settings", transient_for=self.window, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_left(10)
        box.set_margin_right(10)

        # Recordings directory setting
        dir_label = Gtk.Label(label="Recordings Directory:")
        dir_label.set_halign(Gtk.Align.START)
        box.pack_start(dir_label, False, False, 0)

        dir_entry = Gtk.Entry()
        dir_entry.set_text(os.path.expanduser(RECORDINGS_DIR))
        box.pack_start(dir_entry, False, False, 0)

        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_dir = dir_entry.get_text().strip()
            if new_dir:
                self._update_recordings_dir(new_dir)
        dialog.destroy()

    def _update_recordings_dir(self, new_dir):
        """Update the recordings directory in app_config.py"""
        import re
        config_path = os.path.join(os.path.dirname(__file__), "app_config.py")
        try:
            with open(config_path, "r") as f:
                lines = f.readlines()
            with open(config_path, "w") as f:
                for line in lines:
                    if line.strip().startswith("RECORDINGS_DIR"):
                        f.write(f'RECORDINGS_DIR = "{new_dir}"')
                    else:
                        f.write(line)
            print(f"Updated recordings directory to: {new_dir}")
        except Exception as e:
            self._show_error_dialog("Settings Error", f"Could not update recordings directory: {e}")

    def _update_ui_state(self):
        """Update UI based on service availability"""
        if not self.audio_recorder.is_audio_available():
            self.status_label.set_text("❌ No audio device available")
            self.start_button.set_sensitive(False)
            return

        if not self.transcription_service.is_available():
            self.status_label.set_text("❌ Transcription service not available")
            # Recording still works, just no transcription

        if self.audio_recorder.is_audio_available() and self.transcription_service.is_available():
            self.status_label.set_text("✅ Ready to record and transcribe")

    def _on_audio_level(self, level_db):
        """Handle audio level updates"""
        def update_level():
            # Convert dB to 0-1 range for progress bar
            # -80dB = 0.0, -20dB = 1.0
            normalized_level = max(0.0, min(1.0, (level_db + 80) / 60))

            self.level_bar.set_fraction(normalized_level)

            if level_db > -40:
                self.level_bar.set_text(f"Loud ({level_db:.0f}dB)")
            elif level_db > -60:
                self.level_bar.set_text(f"Medium ({level_db:.0f}dB)")
            else:
                self.level_bar.set_text(f"Quiet ({level_db:.0f}dB)")

        # Update UI from main thread
        GLib.idle_add(update_level)

    def _on_start_recording(self, button):
        """Handle start recording button click"""
        if self.is_recording:
            return

        if self.audio_recorder.start_recording():
            self.is_recording = True
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.status_label.set_text("🔴 Recording in progress...")

            # Clear previous transcription
            self.transcript_buffer.set_text("")
        else:
            self._show_error_dialog("Failed to Start Recording",
                                  "Could not start audio recording. Check your microphone.")

    def _on_stop_recording(self, button):
        """Handle stop recording button click"""
        if not self.is_recording:
            return

        self.status_label.set_text("⏹️ Stopping recording...")

        # Stop recording in background thread to avoid blocking UI
        threading.Thread(target=self._stop_recording_worker, daemon=True).start()

    def _stop_recording_worker(self):
        """Worker thread to stop recording and transcribe"""
        try:
            # Stop recording
            recording_path = self.audio_recorder.stop_recording()

            def update_ui_stopped():
                self.is_recording = False
                self.start_button.set_sensitive(True)
                self.stop_button.set_sensitive(False)
                self.level_bar.set_fraction(0.0)
                self.level_bar.set_text("Silent")

            GLib.idle_add(update_ui_stopped)

            if recording_path:
                self.current_recording_path = recording_path

                # Update status
                GLib.idle_add(lambda: self.status_label.set_text("💾 Recording saved. Transcribing..."))

                # Transcribe if service is available
                if self.transcription_service.is_available():
                    result = self.transcription_service.transcribe_file(recording_path)

                    if result and result.text.strip():
                        # Update transcript in UI thread
                        def update_transcript():
                            self.transcript_buffer.set_text(result.text)
                            self.status_label.set_text(f"✅ Transcription complete (confidence: {result.confidence:.0%})")

                            # Auto-copy to clipboard
                            try:
                                pyperclip.copy(result.text)
                                print("Transcript copied to clipboard")
                            except Exception as e:
                                print(f"Could not copy to clipboard: {e}")

                        GLib.idle_add(update_transcript)
                    else:
                        GLib.idle_add(lambda: self.status_label.set_text("⚠️ No speech detected in recording"))
                        GLib.idle_add(lambda: self.transcript_buffer.set_text("(No speech detected)"))
                else:
                    GLib.idle_add(lambda: self.status_label.set_text("💾 Recording saved (transcription not available)"))
            else:
                GLib.idle_add(lambda: self.status_label.set_text("❌ Failed to save recording"))

        except Exception as e:
            print(f"Error in stop recording worker: {e}")
            GLib.idle_add(lambda: self.status_label.set_text("❌ Error processing recording"))

    def _on_copy_transcript(self, button):
        """Handle copy transcript button click"""
        start_iter = self.transcript_buffer.get_start_iter()
        end_iter = self.transcript_buffer.get_end_iter()
        text = self.transcript_buffer.get_text(start_iter, end_iter, False)

        if text.strip():
            try:
                pyperclip.copy(text)
                self._show_info_dialog("Copied", "Transcript copied to clipboard!")
            except Exception as e:
                self._show_error_dialog("Copy Failed", f"Could not copy to clipboard: {e}")
        else:
            self._show_info_dialog("Nothing to Copy", "No transcript text available.")

    def _on_play_recording(self, button):
        """Play the current recording"""
        if self.current_recording_path:
            try:
                os.system(f"ffplay -nodisp -autoexit {self.current_recording_path}")
            except Exception as e:
                self._show_error_dialog("Playback Failed", f"Could not play recording: {e}")
        else:
            self._show_info_dialog("No Recording", "No recording available to play.")

    def _on_import_audio(self, button):
        """Import an audio file"""
        dialog = Gtk.FileChooserDialog(
            title="Select Audio File",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Audio Files")
        filter_audio.add_mime_type("audio/wav")
        filter_audio.add_mime_type("audio/mp3")
        filter_audio.add_mime_type("audio/aac")
        filter_audio.add_mime_type("audio/ogg")
        dialog.add_filter(filter_audio)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            try:
                result = self.transcription_service.transcribe_file(file_path)
                if result and result.text.strip():
                    self.transcript_buffer.set_text(result.text)
                    self.status_label.set_text(f"✅ Transcription complete (confidence: {result.confidence:.0%})")
                else:
                    self.status_label.set_text("⚠️ No speech detected in imported file")
                    self.transcript_buffer.set_text("(No speech detected)")
            except Exception as e:
                self._show_error_dialog("Import Failed", f"Could not transcribe file: {e}")
        dialog.destroy()

    def _show_error_dialog(self, title, message):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def _show_info_dialog(self, title, message):
        """Show info dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def _on_window_destroy(self, window):
        """Handle window destroy event"""
        # Stop recording if in progress
        if self.is_recording:
            self.audio_recorder.stop_recording()

        Gtk.main_quit()

    def run(self):
        """Run the application"""
        self.window.show_all()
        Gtk.main()

# Run the app if executed directly
if __name__ == "__main__":
    app = VoiceRecorderApp()
    app.run()
