"""Tests for session grouping functionality in NDF to text converter."""

import os
import struct
import tempfile

import pytest

from ndf_to_text_converter import group_ndf_files_into_sessions


class TestSessionGrouping:
    """Test cases for session grouping logic."""

    def create_mock_ndf_file(self, directory: str, timestamp: int) -> str:
        """Helper to create a mock NDF file with given timestamp."""
        filename = os.path.join(directory, f"M{timestamp}.ndf")
        with open(filename, "wb") as f:
            f.write(b" ndf")  # Magic bytes
            f.write(b"\x00" * 1000)  # Padding
            # Add some messages to give the file duration
            for i in range(512):  # ~1 second at 512 Hz
                message = struct.pack("<I", i)  # Timestamp
                message += struct.pack("B", 1)  # Channel 1
                message += struct.pack("<H", 32768)  # Data
                message += struct.pack("B", 0)  # Checksum
                f.write(message)
        return filename

    def test_group_single_file(self):
        """Test grouping with a single NDF file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = self.create_mock_ndf_file(temp_dir, 1555404530)

            sessions = group_ndf_files_into_sessions([file1])

            assert len(sessions) == 1
            assert len(sessions[0]) == 1
            assert sessions[0][0] == file1

    def test_group_continuous_files(self):
        """Test grouping continuous files (no gap)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files 1 second apart (no gap)
            file1 = self.create_mock_ndf_file(temp_dir, 1555404530)
            file2 = self.create_mock_ndf_file(temp_dir, 1555404531)
            file3 = self.create_mock_ndf_file(temp_dir, 1555404532)

            sessions = group_ndf_files_into_sessions([file1, file2, file3])

            # Should be one continuous session
            assert len(sessions) == 1
            assert len(sessions[0]) == 3
            assert sessions[0] == [file1, file2, file3]

    def test_group_files_with_gap(self):
        """Test grouping files with a gap larger than threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with large gap (default threshold is 3600 seconds = 1 hour)
            file1 = self.create_mock_ndf_file(temp_dir, 1555404530)
            file2 = self.create_mock_ndf_file(temp_dir, 1555404531)
            # Gap of ~40 days
            file3 = self.create_mock_ndf_file(temp_dir, 1558948567)
            file4 = self.create_mock_ndf_file(temp_dir, 1558948568)

            sessions = group_ndf_files_into_sessions([file1, file2, file3, file4])

            # Should be two sessions
            assert len(sessions) == 2
            assert len(sessions[0]) == 2
            assert sessions[0] == [file1, file2]
            assert len(sessions[1]) == 2
            assert sessions[1] == [file3, file4]

    def test_group_custom_threshold(self):
        """Test grouping with custom gap threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with 10 second gap
            file1 = self.create_mock_ndf_file(temp_dir, 1555404530)
            file2 = self.create_mock_ndf_file(temp_dir, 1555404540)  # +10 seconds

            # With default threshold (3600s), should be one session
            sessions = group_ndf_files_into_sessions([file1, file2])
            assert len(sessions) == 1

            # With threshold of 5 seconds, should be two sessions
            sessions = group_ndf_files_into_sessions([file1, file2], gap_threshold=5.0)
            assert len(sessions) == 2

    def test_group_unsorted_files(self):
        """Test that files are sorted by timestamp before grouping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = self.create_mock_ndf_file(temp_dir, 1555404530)
            file2 = self.create_mock_ndf_file(temp_dir, 1555404531)
            file3 = self.create_mock_ndf_file(temp_dir, 1555404532)

            # Provide files in wrong order
            sessions = group_ndf_files_into_sessions([file3, file1, file2])

            # Should still be sorted correctly in session
            assert len(sessions) == 1
            assert sessions[0] == [file1, file2, file3]

    def test_group_invalid_filename(self):
        """Test that files without valid timestamp are skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid file
            valid_file = self.create_mock_ndf_file(temp_dir, 1555404530)

            # Create invalid file
            invalid_file = os.path.join(temp_dir, "invalid_name.ndf")
            with open(invalid_file, "wb") as f:
                f.write(b" ndf")
                f.write(b"\x00" * 1000)

            sessions = group_ndf_files_into_sessions([valid_file, invalid_file])

            # Should only include valid file
            assert len(sessions) == 1
            assert len(sessions[0]) == 1
            assert sessions[0][0] == valid_file

    def test_group_empty_list(self):
        """Test grouping empty file list."""
        sessions = group_ndf_files_into_sessions([])
        assert sessions == []

    def test_group_multiple_gaps(self):
        """Test grouping with multiple gaps creating multiple sessions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Session 1
            file1 = self.create_mock_ndf_file(temp_dir, 1555404530)
            file2 = self.create_mock_ndf_file(temp_dir, 1555404531)

            # Gap

            # Session 2
            file3 = self.create_mock_ndf_file(temp_dir, 1555500000)
            file4 = self.create_mock_ndf_file(temp_dir, 1555500001)

            # Gap

            # Session 3
            file5 = self.create_mock_ndf_file(temp_dir, 1555600000)

            sessions = group_ndf_files_into_sessions(
                [file1, file2, file3, file4, file5], gap_threshold=3600.0
            )

            assert len(sessions) == 3
            assert sessions[0] == [file1, file2]
            assert sessions[1] == [file3, file4]
            assert sessions[2] == [file5]

    def test_group_chronological_ordering(self):
        """Test that sessions maintain chronological order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files in non-chronological order
            timestamps = [1555404532, 1555404530, 1555404531]
            files = [self.create_mock_ndf_file(temp_dir, ts) for ts in timestamps]

            sessions = group_ndf_files_into_sessions(files)

            # Should be sorted chronologically
            assert len(sessions) == 1
            expected_order = [
                os.path.join(temp_dir, "M1555404530.ndf"),
                os.path.join(temp_dir, "M1555404531.ndf"),
                os.path.join(temp_dir, "M1555404532.ndf"),
            ]
            assert sessions[0] == expected_order


class TestSessionGroupingEdgeCases:
    """Test edge cases for session grouping."""

    def create_mock_ndf_file(self, directory: str, timestamp: int) -> str:
        """Helper to create a mock NDF file."""
        filename = os.path.join(directory, f"M{timestamp}.ndf")
        with open(filename, "wb") as f:
            f.write(b" ndf")
            f.write(b"\x00" * 1000)
        return filename

    def test_gap_exactly_at_threshold(self):
        """Test gap exactly at threshold (should be grouped together)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = self.create_mock_ndf_file(temp_dir, 1555404530)
            # Gap of exactly 3600 seconds
            file2 = self.create_mock_ndf_file(temp_dir, 1555408130)

            sessions = group_ndf_files_into_sessions(
                [file1, file2], gap_threshold=3600.0
            )

            # Gap equal to threshold should create new session
            # (gap > threshold, not gap >= threshold)
            assert len(sessions) == 1

    def test_gap_just_over_threshold(self):
        """Test gap just over threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = self.create_mock_ndf_file(temp_dir, 1555404530)
            # Gap of 3601 seconds (1 over threshold)
            file2 = self.create_mock_ndf_file(temp_dir, 1555408131)

            sessions = group_ndf_files_into_sessions(
                [file1, file2], gap_threshold=3600.0
            )

            # Should create two sessions
            assert len(sessions) == 2
