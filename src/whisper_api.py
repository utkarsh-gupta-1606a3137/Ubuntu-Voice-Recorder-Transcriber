#!/usr/bin/env python3
"""
Whisper API Integration Module
Handles transcription using OpenAI Whisper API
"""

import requests
from typing import Optional
from dataclasses import dataclass

@dataclass
class WhisperTranscriptionResult:
    """Result of Whisper API transcription operation"""
    text: str
    confidence: float
    language: str

class WhisperAPI:
    """Online transcription service using OpenAI Whisper API"""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini-transcribe"):
        """Initialize Whisper API service

        Args:
            api_key: OpenAI API key
            model_name: OpenAI model name for transcription
        """
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"
        self.model_name = model_name

    def transcribe_file(self, file_path: str) -> Optional[WhisperTranscriptionResult]:
        """Transcribe audio file using Whisper API

        Args:
            file_path: Path to audio file

        Returns:
            WhisperTranscriptionResult: Transcription result, or None if error
        """
        try:
            print(f"Using Whisper API for transcription: {file_path}")

            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            files = {
                "file": open(file_path, "rb"),
            }
            data = {
                "model": self.model_name
            }
            response = requests.post(self.api_url, headers=headers, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "").strip()
                language = result.get("language", "en-us")
                confidence = 0.9  # Whisper API does not provide confidence directly

                print(f"Whisper API transcription completed: '{text}'")

                return WhisperTranscriptionResult(
                    text=text,
                    confidence=confidence,
                    language=language
                )
            else:
                print(f"Error from Whisper API: {response.status_code} {response.text}")
                return None

        except Exception as e:
            print(f"Error during Whisper API transcription: {e}")
            return None
