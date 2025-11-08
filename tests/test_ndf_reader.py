"""Tests for NDF reader functionality."""

import struct
import tempfile

import pytest

from ndf_reader import NDFReader, SimpleBinarySignalReader, TextSignalReader


class TestSimpleBinarySignalReader:
    """Test cases for SimpleBinarySignalReader."""

    def test_read_signal_basic(self):
        """Test basic binary signal reading."""
        # Create test binary data
        test_data = [1000, 2000, 3000, 4000, 5000, 6000]
        binary_data = struct.pack(f"<{len(test_data)}H", *test_data)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(binary_data)
            temp_file.flush()

            intervals = SimpleBinarySignalReader.read_signal(
                filepath=temp_file.name,
                sample_rate=2.0,  # 2 Hz for easy testing
                interval_length=1.0,  # 1 second intervals
            )

            # Should have 3 intervals (6 samples / 2 samples per interval)
            assert len(intervals) == 3
            assert intervals[0] == (0.0, [1000, 2000])
            assert intervals[1] == (
                1.0,
                [3000, 4000],
            )  # Timestamp is interval_index * sample_rate
            assert intervals[2] == (2.0, [5000, 6000])

    def test_read_signal_partial_interval(self):
        """Test reading when last interval is partial."""
        # Create test data that doesn't divide evenly
        test_data = [1000, 2000, 3000]
        binary_data = struct.pack(f"<{len(test_data)}H", *test_data)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(binary_data)
            temp_file.flush()

            intervals = SimpleBinarySignalReader.read_signal(
                filepath=temp_file.name, sample_rate=2.0, interval_length=1.0
            )

            # Should have 2 intervals: [1000, 2000] and [3000]
            assert len(intervals) == 2
            assert intervals[0] == (0.0, [1000, 2000])
            assert intervals[1] == (1.0, [3000])

    def test_read_signal_empty_file(self):
        """Test reading empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            intervals = SimpleBinarySignalReader.read_signal(
                filepath=temp_file.name, sample_rate=512.0, interval_length=1.0
            )
            assert intervals == []


class TestTextSignalReader:
    """Test cases for TextSignalReader."""

    def test_read_signal_basic(self):
        """Test basic text signal reading."""
        test_data = "1000\n2000\n3000\n4000\n"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            intervals = TextSignalReader.read_signal(
                filepath=temp_file.name,
                sample_rate=2.0,  # 2 Hz for easy testing
                interval_length=1.0,  # 1 second intervals
            )

            assert len(intervals) == 2
            assert intervals[0] == (0.0, [1000, 2000])
            assert intervals[1] == (1.0, [3000, 4000])

    def test_read_signal_with_comments(self):
        """Test reading text file with comment lines."""
        test_data = """# This is a comment
1000
# Another comment
2000
3000
4000
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            intervals = TextSignalReader.read_signal(
                filepath=temp_file.name, sample_rate=2.0, interval_length=1.0
            )

            assert len(intervals) == 2
            assert intervals[0] == (0.0, [1000, 2000])
            assert intervals[1] == (1.0, [3000, 4000])

    def test_read_signal_with_floats(self):
        """Test reading text file with float values."""
        test_data = "1000.5\n2000.7\n3000.2\n4000.9\n"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            intervals = TextSignalReader.read_signal(
                filepath=temp_file.name, sample_rate=2.0, interval_length=1.0
            )

            # Should convert floats to ints
            assert intervals[0] == (0.0, [1000, 2000])
            assert intervals[1] == (1.0, [3000, 4000])

    def test_read_signal_with_invalid_lines(self):
        """Test reading text file with some invalid lines."""
        test_data = """1000
invalid_line
2000
3000
another_invalid
4000
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            intervals = TextSignalReader.read_signal(
                filepath=temp_file.name, sample_rate=2.0, interval_length=1.0
            )

            # Should skip invalid lines
            assert len(intervals) == 2
            assert intervals[0] == (0.0, [1000, 2000])
            assert intervals[1] == (1.0, [3000, 4000])

    def test_read_signal_empty_file(self):
        """Test reading empty text file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            intervals = TextSignalReader.read_signal(
                filepath=temp_file.name, sample_rate=512.0, interval_length=1.0
            )
            assert intervals == []


class TestNDFReader:
    """Test cases for NDFReader (these would require mock NDF data)."""

    def test_init_with_invalid_file(self):
        """Test NDFReader initialization with non-existent file."""
        with pytest.raises(FileNotFoundError):
            NDFReader("non_existent_file.ndf")

    def test_metadata_defaults(self):
        """Test that metadata has sensible defaults."""
        # Create a minimal mock NDF file
        with tempfile.NamedTemporaryFile(suffix=".ndf", delete=False) as temp_file:
            # Write minimal NDF header
            temp_file.write(b" ndf")  # Magic bytes
            temp_file.write(b"\x00" * 12)  # Header padding
            temp_file.write(b"\x00" * 500)  # More padding
            temp_file.flush()

            reader = NDFReader(temp_file.name)
            assert reader.filepath == temp_file.name
            assert isinstance(reader.metadata, dict)
            assert reader.message_size == 8
            assert reader.data_start_offset is not None

    def test_get_creation_date_unknown(self):
        """Test get_creation_date with no metadata."""
        with tempfile.NamedTemporaryFile(suffix=".ndf", delete=False) as temp_file:
            temp_file.write(b" ndf")
            temp_file.write(b"\x00" * 1000)
            temp_file.flush()

            reader = NDFReader(temp_file.name)
            creation_date = reader.get_creation_date()
            # Should return 'Unknown' or current date
            assert isinstance(creation_date, str)
            assert len(creation_date) > 0
