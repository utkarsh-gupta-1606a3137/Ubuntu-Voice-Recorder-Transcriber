# Ubuntu Voice Recording Application

A basic Ubuntu desktop application for voice recording and transcription using Python+GTK.

## Features

- Simple GUI with Start/Stop recording buttons
- Audio recording in WAV format
- Offline transcription using Vosk speech recognition
- Automatic clipboard copying of transcription results
- Native Ubuntu integration with GTK

## Requirements

- Ubuntu 20.04 LTS or later
- Python 3.8+
- Microphone access
- Internet connection (for initial Vosk model download)

## Installation

1. Install system dependencies:
```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 portaudio19-dev python3-dev
```

2. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

3. Download Vosk model (done automatically on first run)

4. Set up sensitive configuration:

```bash
python3 setup_secrets.py
# Then edit secrets_config.py to add your info
```
   - fill in your OpenAI API key and device paths, or run:

## Usage

Run the application:
```bash
python3 main.py
```

1. Click "Start Recording" to begin recording
2. Speak into your microphone
3. Click "Stop Recording" to end recording
4. Wait for transcription to complete
5. Transcription will appear in the text area and be copied to clipboard

## Desktop Integration

To generate a `.desktop` launcher file (using your device paths from secrets_config.py):
```bash
python3 generate_desktop_file.py
```
This will create `VoiceRecorder.desktop` for easy launching from your desktop environment.

## Security & Configuration

- Sensitive info (API keys, device paths) is stored in `secrets_config.py`, which is ignored by git.
- Only `secrets_config.example.py` is tracked in git for sharing safe defaults.
- General app settings are in `src/app_config.py`.

## Recordings

Audio files are saved to the directory specified in `src/app_config.py` (default: `/tmp/Recordings`).

## Troubleshooting

- Ensure microphone is connected and working
- Check audio permissions in Ubuntu Settings
- Verify PulseAudio/PipeWire is running
- Check that Python dependencies are installed correctly
