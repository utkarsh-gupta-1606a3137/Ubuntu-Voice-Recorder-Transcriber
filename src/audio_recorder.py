#!/usr/bin/env python3
"""
Audio Recording Module
Handles audio capture using PyAudio with WAV output
"""

import pyaudio
import wave
import os
import threading
import time
from datetime import datetime
from typing import Callable, Optional

class AudioRecorder:
    """Handles audio recording with PyAudio backend"""

    def __init__(self, recordings_dir: str = None):
        """Initialize audio recorder

        Args:
            recordings_dir: Directory to save recordings (default: ~/Recordings)
        """
        self.recordings_dir = recordings_dir or os.path.expanduser("~/Recordings")
        self.sample_rate = 16000  # 16kHz for Vosk compatibility
        self.channels = 1  # Mono
        self.chunk_size = 1024
        self.format = pyaudio.paInt16

        # Recording state
        self.is_recording = False
        self.audio_data = []
        self.pyaudio_instance = None
        self.stream = None
        self.recording_thread = None
        self.level_callback = None

        # Create recordings directory if it doesn't exist
        self._create_recordings_directory()

    def _create_recordings_directory(self):
        """Create recordings directory if it doesn't exist"""
        try:
            os.makedirs(self.recordings_dir, mode=0o700, exist_ok=True)
            print(f"Recordings directory: {self.recordings_dir}")
        except OSError as e:
            print(f"Error creating recordings directory: {e}")
            # Fallback to current directory
            self.recordings_dir = "."

    def _calculate_audio_level(self, audio_chunk):
        """Calculate audio level in dB from chunk data"""
        try:
            import numpy as np
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            # Calculate RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_array**2))
            # Convert to dB (avoid log(0) by adding small value)
            if rms > 0:
                db = 20 * np.log10(rms / 32767.0)  # 32767 is max value for int16
            else:
                db = -80  # Very quiet
            return max(db, -80)  # Clamp minimum at -80dB
        except:
            return -80  # Return quiet level on error

    def _recording_worker(self):
        """Worker thread for audio recording"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()

            # Open audio stream
            self.stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            print("Recording started...")
            self.audio_data = []

            while self.is_recording:
                try:
                    # Read audio chunk
                    audio_chunk = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_data.append(audio_chunk)

                    # Calculate and report audio level if callback is set
                    if self.level_callback:
                        level_db = self._calculate_audio_level(audio_chunk)
                        self.level_callback(level_db)

                except Exception as e:
                    print(f"Error reading audio: {e}")
                    break

        except Exception as e:
            print(f"Error initializing audio: {e}")
            self.is_recording = False
        finally:
            self._cleanup_audio()

    def _cleanup_audio(self):
        """Clean up audio resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None

        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
            self.pyaudio_instance = None

    def start_recording(self) -> bool:
        """Start recording audio

        Returns:
            bool: True if recording started successfully
        """
        if self.is_recording:
            print("Already recording")
            return False

        try:
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._recording_worker)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[str]:
        """Stop recording and save to file

        Returns:
            str: Path to saved file, or None if error
        """
        if not self.is_recording:
            print("Not currently recording")
            return None

        self.is_recording = False

        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)

        # Save audio data to file
        if self.audio_data:
            return self._save_audio_data()
        else:
            print("No audio data to save")
            return None

    def _save_audio_data(self) -> Optional[str]:
        """Save recorded audio data to WAV file

        Returns:
            str: Path to saved file, or None if error
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            filepath = os.path.join(self.recordings_dir, filename)

            # Save as WAV file
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.audio_data))

            file_size = os.path.getsize(filepath)
            duration = len(self.audio_data) * self.chunk_size / self.sample_rate

            print(f"Recording saved: {filepath}")
            print(f"Duration: {duration:.1f}s, Size: {file_size} bytes")

            return filepath

        except Exception as e:
            print(f"Error saving audio file: {e}")
            return None

    def on_level(self, callback: Callable[[float], None]) -> None:
        """Register callback for audio level updates

        Args:
            callback: Function to call with dB level (float)
        """
        self.level_callback = callback

    def is_audio_available(self) -> bool:
        """Check if audio input is available

        Returns:
            bool: True if audio input is available
        """
        try:
            p = pyaudio.PyAudio()
            # Try to get default input device
            device_info = p.get_default_input_device_info()
            p.terminate()
            return device_info is not None
        except:
            return False

# Test the audio recorder if run directly
if __name__ == "__main__":
    print("Testing AudioRecorder...")

    recorder = AudioRecorder()

    if not recorder.is_audio_available():
        print("No audio input device available!")
        exit(1)

    print("Audio device found. Testing recording for 3 seconds...")

    # Test level callback
    def level_callback(db):
        print(f"Level: {db:.1f} dB")

    recorder.on_level(level_callback)

    # Start recording
    if recorder.start_recording():
        print("Recording... (3 seconds)")
        time.sleep(3)

        # Stop and save
        filepath = recorder.stop_recording()
        if filepath:
            print(f"Test recording saved to: {filepath}")
        else:
            print("Failed to save recording")
    else:
        print("Failed to start recording")
