"""Tests for NDF to text converter functionality."""

import os
import struct
import tempfile

import pytest

from ndf_to_text_converter import NDFToTextConverter, bulk_convert_ndf_to_text
from tests.ndf_test_utils import create_multi_channel_ndf_file, create_valid_ndf_file


class TestNDFToTextConverter:
    """Test cases for NDFToTextConverter class."""

    def test_init_default_values(self):
        """Test NDFToTextConverter initialization with default values."""
        converter = NDFToTextConverter()
        assert converter.output_format == "simple"
        assert converter.include_timestamps is False
        assert converter.include_metadata is True

    def test_init_custom_values(self):
        """Test NDFToTextConverter initialization with custom values."""
        converter = NDFToTextConverter(
            output_format="detailed",
            include_timestamps=True,
            include_metadata=False,
        )
        assert converter.output_format == "detailed"
        assert converter.include_timestamps is True
        assert converter.include_metadata is False


class TestConvertNDFFile:
    """Test cases for convert_ndf_file functionality."""

    def test_convert_ndf_file_simple_format(self):
        """Test converting NDF file with simple format."""
        converter = NDFToTextConverter(output_format="simple")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock NDF file
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")
            create_valid_ndf_file(ndf_file, channel=1, num_messages=50)

            output_dir = os.path.join(temp_dir, "output")

            created_files = converter.convert_ndf_file(
                input_file=ndf_file,
                output_dir=output_dir,
                channels=[1],
            )

            # Should create E1.txt
            assert len(created_files) == 1
            assert os.path.exists(created_files[0])
            assert "E1.txt" in created_files[0]

    def test_convert_ndf_file_with_metadata(self):
        """Test that metadata is included in output when requested."""
        converter = NDFToTextConverter(output_format="simple", include_metadata=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")
            create_valid_ndf_file(ndf_file, channel=1, num_messages=20)

            output_dir = os.path.join(temp_dir, "output")

            created_files = converter.convert_ndf_file(
                input_file=ndf_file,
                output_dir=output_dir,
                channels=[1],
            )

            # Check file contains metadata header
            with open(created_files[0], "r") as f:
                content = f.read()
                assert "# NDF to Text Conversion" in content
                assert "# Channel: 1" in content

    def test_convert_ndf_file_without_metadata(self):
        """Test that metadata is excluded when not requested."""
        converter = NDFToTextConverter(output_format="simple", include_metadata=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")
            create_valid_ndf_file(ndf_file, channel=1, num_messages=20)

            output_dir = os.path.join(temp_dir, "output")

            created_files = converter.convert_ndf_file(
                input_file=ndf_file,
                output_dir=output_dir,
                channels=[1],
            )

            # Check file doesn't contain metadata header
            with open(created_files[0], "r") as f:
                content = f.read()
                assert "# NDF to Text Conversion" not in content

    def test_convert_ndf_file_detailed_format(self):
        """Test converting with detailed format."""
        converter = NDFToTextConverter(output_format="detailed", include_metadata=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")
            create_valid_ndf_file(ndf_file, channel=1, num_messages=20)

            output_dir = os.path.join(temp_dir, "output")

            created_files = converter.convert_ndf_file(
                input_file=ndf_file,
                output_dir=output_dir,
                channels=[1],
            )

            # Check file contains detailed format markers
            with open(created_files[0], "r") as f:
                content = f.read()
                assert "Detailed Format" in content
                assert "Interval start:" in content

    def test_convert_ndf_file_csv_format(self):
        """Test converting with CSV format."""
        converter = NDFToTextConverter(output_format="csv", include_timestamps=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")
            create_valid_ndf_file(ndf_file, channel=1, num_messages=20)

            output_dir = os.path.join(temp_dir, "output")

            created_files = converter.convert_ndf_file(
                input_file=ndf_file,
                output_dir=output_dir,
                channels=[1],
            )

            # Check file contains CSV header
            with open(created_files[0], "r") as f:
                first_line = f.readline()
                assert "interval_time" in first_line
                assert "sample_value" in first_line

    def test_convert_ndf_file_csv_with_timestamps(self):
        """Test CSV format with timestamps."""
        converter = NDFToTextConverter(output_format="csv", include_timestamps=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")
            create_valid_ndf_file(ndf_file, channel=1, num_messages=20)

            output_dir = os.path.join(temp_dir, "output")

            created_files = converter.convert_ndf_file(
                input_file=ndf_file,
                output_dir=output_dir,
                channels=[1],
            )

            # Check file contains timestamp column
            with open(created_files[0], "r") as f:
                first_line = f.readline()
                assert "timestamp" in first_line


class TestBulkConversion:
    """Test cases for bulk conversion functionality."""

    def test_find_ndf_files_single_file(self):
        """Test finding a single NDF file."""
        from ndf_to_text_converter import find_ndf_files

        with tempfile.NamedTemporaryFile(suffix=".ndf", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            files = find_ndf_files(temp_path)
            assert len(files) == 1
            assert files[0] == temp_path
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_find_ndf_files_directory(self):
        """Test finding NDF files in a directory."""
        from ndf_to_text_converter import find_ndf_files

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test NDF files
            ndf_files = []
            for i in range(3):
                file_path = os.path.join(temp_dir, f"test{i}.ndf")
                with open(file_path, "w") as f:
                    f.write("test")
                ndf_files.append(file_path)

            found_files = find_ndf_files(temp_dir)
            assert len(found_files) == 3
            assert sorted(found_files) == sorted(ndf_files)

    def test_find_ndf_files_mixed_extensions(self):
        """Test finding NDF files among other file types."""
        from ndf_to_text_converter import find_ndf_files

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create NDF file
            ndf_file = os.path.join(temp_dir, "test.ndf")
            with open(ndf_file, "w") as f:
                f.write("test")

            # Create non-NDF files
            for ext in [".txt", ".csv", ".dat"]:
                with open(os.path.join(temp_dir, f"other{ext}"), "w") as f:
                    f.write("test")

            found_files = find_ndf_files(temp_dir)
            assert len(found_files) == 1
            assert found_files[0] == ndf_file

    def test_find_ndf_files_uppercase_extension(self):
        """Test finding NDF files with uppercase extension."""
        from ndf_to_text_converter import find_ndf_files

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with different case extensions
            ndf_lower = os.path.join(temp_dir, "test_lower.ndf")
            ndf_upper = os.path.join(temp_dir, "test_upper.NDF")

            with open(ndf_lower, "w") as f:
                f.write("test")
            with open(ndf_upper, "w") as f:
                f.write("test")

            found_files = find_ndf_files(temp_dir)
            assert len(found_files) == 2

    def test_find_ndf_files_invalid_path(self):
        """Test error handling for invalid path."""
        from ndf_to_text_converter import find_ndf_files

        with pytest.raises(FileNotFoundError):
            find_ndf_files("/nonexistent/path/to/files")

    def test_find_ndf_files_non_ndf_file(self):
        """Test error handling for non-NDF file."""
        from ndf_to_text_converter import find_ndf_files

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            with pytest.raises(ValueError):
                find_ndf_files(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_find_ndf_files_empty_directory(self):
        """Test finding NDF files in empty directory."""
        from ndf_to_text_converter import find_ndf_files

        with tempfile.TemporaryDirectory() as temp_dir:
            found_files = find_ndf_files(temp_dir)
            assert len(found_files) == 0


class TestBulkConvertWithSessions:
    """Test cases for bulk conversion with session grouping."""

    def test_bulk_convert_empty_directory(self):
        """Test bulk conversion with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            results = bulk_convert_ndf_to_text(
                input_path=temp_dir,
                channels=[1],
            )
            assert results == {}

    def test_bulk_convert_single_file(self):
        """Test bulk conversion with single file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")
            create_valid_ndf_file(ndf_file, channel=1)

            results = bulk_convert_ndf_to_text(
                input_path=temp_dir,
                channels=[1],
            )

            # Should create one session
            assert len(results) == 1
            assert "session_1555404530" in results

    def test_bulk_convert_custom_output_dir(self):
        """Test bulk conversion with custom output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")
            create_valid_ndf_file(ndf_file, channel=1)

            output_dir = os.path.join(temp_dir, "custom_output")

            results = bulk_convert_ndf_to_text(
                input_path=temp_dir,
                output_dir=output_dir,
                channels=[1],
            )

            # Check output directory was created
            assert os.path.exists(output_dir)

    def test_bulk_convert_all_channels(self):
        """Test bulk conversion extracting all channels."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ndf_file = os.path.join(temp_dir, "M1555404530.ndf")

            # Create file with multiple channels
            create_multi_channel_ndf_file(ndf_file, channel_messages=[(0, 20), (1, 20)])

            results = bulk_convert_ndf_to_text(
                input_path=temp_dir,
                channels=None,  # Extract all channels
            )

            # Should have created files for both channels
            assert len(results) == 1
