"""Tests for NDF to text converter functionality."""

import os
import tempfile

import pytest

from ndf_to_text_converter import NDFToTextConverter


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

    def test_output_directory_structure(self):
        """Test that files are output to subdirectories with E{channel}.txt naming."""
        # This test would require a mock NDF file or mock NDFReader
        # For now, we document the expected behavior
        # Expected: output_dir/base_name/E{channel}.txt
        pass

    def test_channel_naming_convention(self):
        """Test that channel files use E{channel}.txt naming convention."""
        # Expected output format: E0.txt, E1.txt, E15.txt
        # Not: base_name_ch00.txt, base_name_ch01.txt
        pass


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
