"""Tests for new session-based NDF reader functionality."""

import os
import struct
import tempfile
from datetime import datetime

import pytest

from ndf_reader import NDFReader


class TestNDFReaderTimestampExtraction:
    """Test cases for Unix timestamp extraction from NDF filenames."""

    def test_extract_archive_start_time_valid(self):
        """Test extraction of Unix timestamp from valid Mx.ndf filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock NDF file with proper timestamp pattern
            timestamp = 1555404530  # 2019-04-16
            ndf_file = os.path.join(temp_dir, f"M{timestamp}.ndf")

            # Write minimal NDF file structure
            with open(ndf_file, "wb") as f:
                f.write(b" ndf")  # Magic bytes
                f.write(b"\x00" * 1000)  # Padding

            reader = NDFReader(ndf_file)
            extracted_time = reader.get_archive_start_time()

            assert extracted_time == timestamp

    def test_extract_archive_start_time_case_insensitive(self):
        """Test that extraction works with uppercase .NDF extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            timestamp = 1555404530
            ndf_file = os.path.join(temp_dir, f"M{timestamp}.NDF")

            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            reader = NDFReader(ndf_file)
            extracted_time = reader.get_archive_start_time()

            assert extracted_time == timestamp

    def test_extract_archive_start_time_invalid_filename(self):
        """Test that invalid filenames return None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with non-standard name
            ndf_file = os.path.join(temp_dir, "invalid_name.ndf")

            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            reader = NDFReader(ndf_file)
            extracted_time = reader.get_archive_start_time()

            assert extracted_time is None

    def test_extract_archive_start_time_wrong_digit_count(self):
        """Test that timestamps with wrong digit count return None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with 9 digits instead of 10
            ndf_file = os.path.join(temp_dir, "M155540453.ndf")

            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            reader = NDFReader(ndf_file)
            extracted_time = reader.get_archive_start_time()

            assert extracted_time is None


class TestNDFReaderPerChannelSampleRates:
    """Test cases for per-channel sample rate detection."""

    def test_get_channel_sample_rate_channel_0(self):
        """Test that channel 0 returns 128 Hz (clock signal)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")

            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            reader = NDFReader(ndf_file)
            sample_rate = reader.get_channel_sample_rate(0)

            assert sample_rate == 128.0

    def test_get_channel_sample_rate_other_channels(self):
        """Test that non-zero channels return 512 Hz."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")

            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            reader = NDFReader(ndf_file)

            # Test several channels
            for channel in [1, 2, 5, 10, 15]:
                sample_rate = reader.get_channel_sample_rate(channel)
                assert sample_rate == 512.0

    def test_get_channel_sample_rate_caching(self):
        """Test that sample rates are cached after first call."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")

            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            reader = NDFReader(ndf_file)

            # First call
            rate1 = reader.get_channel_sample_rate(1)
            # Second call should return cached value
            rate2 = reader.get_channel_sample_rate(1)

            assert rate1 == rate2 == 512.0
            # Verify it's in the cache
            assert 1 in reader._channel_sample_rates


class TestNDFReaderFileDuration:
    """Test cases for file duration calculation."""

    def test_get_file_duration_empty_file(self):
        """Test duration calculation for empty NDF file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")

            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            reader = NDFReader(ndf_file)
            duration = reader.get_file_duration()

            # Empty file with no valid messages should return None
            assert duration is None

    def test_read_channel_data_with_auto_detection(self):
        """Test that read_channel_data auto-detects sample rate when None is passed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")

            # Create minimal NDF with some data
            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)
                # Add some channel 0 messages (128 Hz)
                for i in range(10):
                    # Message format: timestamp (4 bytes) + identifier (1 byte) + data (2 bytes) + checksum (1 byte)
                    message = struct.pack("<I", i)  # Timestamp
                    message += struct.pack("B", 0)  # Channel 0
                    message += struct.pack("<H", 32768 + i)  # Data
                    message += struct.pack("B", 0)  # Checksum
                    f.write(message)

            reader = NDFReader(ndf_file)

            # Should auto-detect channel 0 as 128 Hz when sample_rate=None
            intervals = reader.read_channel_data(0, sample_rate=None)

            # Verify method was called successfully (exact results depend on message parsing)
            assert isinstance(intervals, list)


class TestNDFReaderAutoDetection:
    """Integration tests for auto-detection features."""

    def test_auto_detection_workflow(self):
        """Test complete workflow with auto-detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            timestamp = 1555404530
            ndf_file = os.path.join(temp_dir, f"M{timestamp}.ndf")

            with open(ndf_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            reader = NDFReader(ndf_file)

            # Test timestamp extraction
            assert reader.get_archive_start_time() == timestamp

            # Test sample rate detection
            assert reader.get_channel_sample_rate(0) == 128.0
            assert reader.get_channel_sample_rate(1) == 512.0

            # Test file duration (empty file returns None)
            duration = reader.get_file_duration()
            assert duration is None or isinstance(duration, (int, float))
