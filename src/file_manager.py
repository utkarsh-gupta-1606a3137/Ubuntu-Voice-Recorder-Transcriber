#!/usr/bin/env python3
"""
File Manager Module
Handles file operations for recordings
"""

import os
import time
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class RecordingMetadata:
    """Metadata for a recording file"""
    filename: str
    path: str
    size_bytes: int
    duration_ms: int
    created_at: datetime

class FileManager:
    """Manages file operations for recordings"""

    def __init__(self, recordings_dir: str = None):
        """Initialize file manager

        Args:
            recordings_dir: Directory containing recordings (default: ~/Recordings)
        """
        self.recordings_dir = recordings_dir or os.path.expanduser("~/Recordings")

        # Ensure directory exists
        os.makedirs(self.recordings_dir, mode=0o700, exist_ok=True)

    def save(self, blob_data: bytes, filename: str) -> str:
        """Save audio blob to file

        Args:
            blob_data: Raw audio data
            filename: Name of file to save

        Returns:
            str: Full path to saved file
        """
        filepath = os.path.join(self.recordings_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(blob_data)

        # Set file permissions to user-only
        os.chmod(filepath, 0o600)

        return filepath

    def list(self) -> List[RecordingMetadata]:
        """List all recordings with metadata

        Returns:
            List[RecordingMetadata]: List of recording metadata
        """
        recordings = []

        try:
            for filename in os.listdir(self.recordings_dir):
                if filename.endswith('.wav'):
                    filepath = os.path.join(self.recordings_dir, filename)

                    try:
                        stat_info = os.stat(filepath)
                        size_bytes = stat_info.st_size
                        created_at = datetime.fromtimestamp(stat_info.st_mtime)

                        # Estimate duration from file size (rough calculation)
                        # For 16-bit mono at 16kHz: bytes per second = 16000 * 2 = 32000
                        duration_ms = int((size_bytes / 32000) * 1000)

                        metadata = RecordingMetadata(
                            filename=filename,
                            path=filepath,
                            size_bytes=size_bytes,
                            duration_ms=duration_ms,
                            created_at=created_at
                        )
                        recordings.append(metadata)

                    except OSError:
                        # Skip files we can't access
                        continue

        except OSError:
            # Directory doesn't exist or can't be accessed
            pass

        # Sort by creation time (newest first)
        recordings.sort(key=lambda x: x.created_at, reverse=True)
        return recordings

    def delete(self, filename: str) -> bool:
        """Delete a recording file

        Args:
            filename: Name of file to delete

        Returns:
            bool: True if file was deleted successfully
        """
        filepath = os.path.join(self.recordings_dir, filename)

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted: {filename}")
                return True
            else:
                print(f"File not found: {filename}")
                return False
        except OSError as e:
            print(f"Error deleting {filename}: {e}")
            return False

    def cleanup_retention(self, days: int) -> int:
        """Clean up recordings older than specified days

        Args:
            days: Number of days to retain recordings

        Returns:
            int: Number of files deleted
        """
        if days <= 0:
            return 0

        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0

        recordings = self.list()

        for recording in recordings:
            if recording.created_at < cutoff_time:
                if self.delete(recording.filename):
                    deleted_count += 1

        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old recordings (older than {days} days)")

        return deleted_count

    def get_total_size(self) -> int:
        """Get total size of all recordings in bytes

        Returns:
            int: Total size in bytes
        """
        recordings = self.list()
        return sum(r.size_bytes for r in recordings)

    def get_recording_path(self, filename: str) -> Optional[str]:
        """Get full path for a recording filename

        Args:
            filename: Recording filename

        Returns:
            str: Full path if file exists, None otherwise
        """
        filepath = os.path.join(self.recordings_dir, filename)
        return filepath if os.path.exists(filepath) else None

# Test the file manager if run directly
if __name__ == "__main__":
    print("Testing FileManager...")

    manager = FileManager()

    # List existing recordings
    recordings = manager.list()
    print(f"Found {len(recordings)} recordings:")

    for recording in recordings:
        print(f"  {recording.filename}")
        print(f"    Size: {recording.size_bytes} bytes")
        print(f"    Duration: {recording.duration_ms/1000:.1f}s")
        print(f"    Created: {recording.created_at}")
        print()

    total_size = manager.get_total_size()
    print(f"Total storage used: {total_size} bytes ({total_size/1024/1024:.1f} MB)")
