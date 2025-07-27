#!/usr/bin/env python3
"""
Transcription Service Module
Handles offline speech-to-text using Vosk
"""

import json
import os
import wave
import subprocess
from typing import Optional
from dataclasses import dataclass
import requests


from whisper_api import WhisperAPI
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from secrets_config import OPENAI_API_KEY

def is_online() -> bool:
    """Check if the device is online by pinging a reliable server"""
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

try:
    import vosk
except ImportError:
    print("Error: vosk module not found. Please install with: pip install vosk")
    exit(1)

@dataclass
class TranscriptionResult:
    """Result of transcription operation"""
    text: str
    confidence: float
    language: str

class TranscriptionService:
    """Offline STT service using Vosk"""

    def __init__(self, model_path: str = None, api_key: Optional[str] = None):
        """Initialize transcription service

        Args:
            model_path: Path to Vosk model directory
            api_key: OpenAI GPT-4o Mini Transcribe API key
        """
        self.model_path = model_path or self._find_default_model()
        self.model = None
        self.recognizer = None
        self.api_key = api_key or OPENAI_API_KEY
        self.gpt_api = WhisperAPI(self.api_key, model_name="gpt-4o-mini-transcribe")
        if self.model_path:
            self._load_model()

    def _find_default_model(self) -> Optional[str]:
        """Find the default Vosk model in models directory

        Returns:
            str: Path to model directory, or None if not found
        """
        models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

        # Look for Vosk model directories
        if os.path.exists(models_dir):
            for item in os.listdir(models_dir):
                item_path = os.path.join(models_dir, item)
                if os.path.isdir(item_path) and item.startswith("vosk-model"):
                    # Check if it contains required files
                    if self._is_valid_model_dir(item_path):
                        print(f"Found Vosk model: {item_path}")
                        return item_path

        print("No Vosk model found in models directory")
        return None

    def _is_valid_model_dir(self, model_path: str) -> bool:
        """Check if directory contains a valid Vosk model

        Args:
            model_path: Path to potential model directory

        Returns:
            bool: True if directory contains valid model files
        """
        required_files = ["am/final.mdl", "conf/mfcc.conf"]
        required_dirs = ["graph"]

        for file_path in required_files:
            if not os.path.exists(os.path.join(model_path, file_path)):
                return False

        for dir_path in required_dirs:
            if not os.path.isdir(os.path.join(model_path, dir_path)):
                return False

        return True

    def _load_model(self) -> bool:
        """Load the Vosk model

        Returns:
            bool: True if model loaded successfully
        """
        try:
            print(f"Loading Vosk model from: {self.model_path}")

            # Set Vosk log level to reduce output
            vosk.SetLogLevel(-1)

            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)  # 16kHz sample rate

            print("Vosk model loaded successfully")
            return True

        except Exception as e:
            print(f"Error loading Vosk model: {e}")
            self.model = None
            self.recognizer = None
            return False

    def is_available(self) -> bool:
        """Check if transcription service is available

        Returns:
            bool: True if service is ready for transcription
        """
        return self.model is not None and self.recognizer is not None

    def preprocess_audio(self, input_path: str, output_path: str) -> str:
        """Preprocess audio file for better transcription

        Args:
            input_path: Path to input audio file
            output_path: Path to output preprocessed audio file

        Returns:
            str: Path to preprocessed audio file
        """
        try:
            # Use FFmpeg to normalize audio and preserve voice clarity
            command = [
                "ffmpeg", "-i", input_path,
                "-af", "loudnorm,highpass=f=100,lowpass=f=8000",
                "-ar", "16000", "-ac", "1", output_path
            ]
            subprocess.run(command, check=True)
            print(f"Audio preprocessed: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error preprocessing audio: {e}")
            return input_path

    def transcribe_file(self, wav_file_path: str) -> Optional[TranscriptionResult]:
        """Transcribe audio from WAV file using GPT-4o Mini Transcribe API if online, otherwise fallback to offline Vosk model.

        Args:
            wav_file_path: Path to WAV audio file

        Returns:
            TranscriptionResult: Transcription result, or None if error
        """
        if not os.path.exists(wav_file_path):
            print(f"Audio file not found: {wav_file_path}")
            return None

        if is_online():
            result = self.gpt_api.transcribe_file(wav_file_path)
            if result:
                print("[ONLINE] Used OpenAI GPT-4o Mini Transcribe API for transcription.")
                return TranscriptionResult(
                    text=result.text,
                    confidence=result.confidence,
                    language=result.language
                )
            else:
                print("[ONLINE] GPT-4o Mini Transcribe API failed, falling back to offline Vosk model.")

        if not self.is_available():
            print("[OFFLINE] Offline transcription service not available")
            return None

        try:
            print("[OFFLINE] Using offline Vosk model for transcription.")
            print(f"Transcribing: {wav_file_path}")
            preprocessed_path = self.preprocess_audio(wav_file_path, "temp_normalized.wav")
            with wave.open(preprocessed_path, 'rb') as wf:
                print(f"Audio format: {wf.getnchannels()} channels, {wf.getsampwidth()}-bit, {wf.getframerate()}Hz")
                if wf.getnchannels() != 1:
                    print("Error: Audio must be mono (1 channel)")
                    return None
                if wf.getsampwidth() != 2:
                    print("Error: Audio must be 16-bit")
                    return None
                if wf.getframerate() != 16000:
                    print(f"Warning: Audio sample rate is {wf.getframerate()}Hz, expected 16000Hz")
                chunk_size = 4000
                full_result = ""
                while True:
                    data = wf.readframes(chunk_size)
                    if len(data) == 0:
                        break
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').strip()
                        if text:
                            full_result += text + " "
                final_result = json.loads(self.recognizer.FinalResult())
                final_text = final_result.get('text', '').strip()
                if final_text:
                    full_result += final_text
                full_result = full_result.strip()
                if not full_result:
                    print("No speech detected in audio")
                    return TranscriptionResult(
                        text="",
                        confidence=0.0,
                        language="en-us"
                    )
                confidence = self._estimate_confidence(full_result)
                print(f"Transcription completed: '{full_result}'")
                print("[OFFLINE] Used Vosk offline model for transcription.")
                return TranscriptionResult(
                    text=full_result,
                    confidence=confidence,
                    language="en-us"
                )
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None

    def _estimate_confidence(self, text: str) -> float:
        """Estimate confidence based on text characteristics

        Args:
            text: Transcribed text

        Returns:
            float: Estimated confidence (0.0 to 1.0)
        """
        if not text:
            return 0.0

        # Simple heuristic: longer text with recognizable words gets higher confidence
        words = text.split()
        word_count = len(words)

        if word_count == 0:
            return 0.0
        elif word_count < 3:
            return 0.6  # Short utterances are less reliable
        elif word_count < 10:
            return 0.8
        else:
            return 0.9  # Longer utterances usually more reliable

    def transcribe_audio_data(self, audio_data: bytes, sample_rate: int = 16000) -> Optional[TranscriptionResult]:
        """Transcribe audio from raw data

        Args:
            audio_data: Raw audio data (16-bit PCM)
            sample_rate: Sample rate of audio data

        Returns:
            TranscriptionResult: Transcription result, or None if error
        """
        if not self.is_available():
            print("Transcription service not available")
            return None

        if sample_rate != 16000:
            print(f"Warning: Sample rate {sample_rate}Hz may not work optimally (expected 16000Hz)")

        try:
            print("Transcribing audio data...")

            # Process the audio data
            if self.recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '').strip()
            else:
                # Get partial result
                result = json.loads(self.recognizer.PartialResult())
                text = result.get('partial', '').strip()

            # Get final result
            final_result = json.loads(self.recognizer.FinalResult())
            final_text = final_result.get('text', '').strip()

            # Combine results
            full_text = (text + " " + final_text).strip()

            if not full_text:
                print("No speech detected in audio data")
                return TranscriptionResult(
                    text="",
                    confidence=0.0,
                    language="en-us"
                )

            confidence = self._estimate_confidence(full_text)

            print(f"Transcription completed: '{full_text}'")

            return TranscriptionResult(
                text=full_text,
                confidence=confidence,
                language="en-us"
            )

        except Exception as e:
            print(f"Error during transcription: {e}")
            return None

# Test the transcription service if run directly
if __name__ == "__main__":
    print("Testing TranscriptionService...")

    service = TranscriptionService()

    if not service.is_available():
        print("Transcription service not available!")
        print("Make sure Vosk model is downloaded and available in models directory")
        exit(1)

    print("Transcription service ready!")

    # Test with existing recording if available
    recordings_dir = os.path.expanduser("~/Recordings")
    if os.path.exists(recordings_dir):
        wav_files = [f for f in os.listdir(recordings_dir) if f.endswith('.wav')]

        if wav_files:
            test_file = os.path.join(recordings_dir, wav_files[0])
            print(f"\nTesting with: {test_file}")

            result = service.transcribe_file(test_file)
            if result:
                print(f"Result: '{result.text}'")
                print(f"Confidence: {result.confidence:.2f}")
                print(f"Language: {result.language}")
            else:
                print("Transcription failed")
        else:
            print("No WAV files found in recordings directory for testing")
    else:
        print("No recordings directory found for testing")
