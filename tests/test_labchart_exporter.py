"""Tests for LabChart exporter functionality."""

import os
import tempfile

import pytest

from labchart_exporter import LabChartExporter


class TestLabChartExporter:
    """Test cases for LabChartExporter class."""

    def test_init_default_values(self):
        """Test LabChartExporter initialization with default values."""
        exporter = LabChartExporter()
        assert exporter.sample_rate == 512.0
        assert exporter.range_mV == 120.0
        assert exporter.use_commas is False
        assert exporter.time_in_ms is False
        assert exporter.value_in_uV is False
        assert exporter.absolute_time is False
        assert exporter.glitch_threshold == 500

    def test_init_custom_values(self):
        """Test LabChartExporter initialization with custom values."""
        exporter = LabChartExporter(
            sample_rate=1024.0,
            range_mV=30.0,
            use_commas=True,
            time_in_ms=True,
            value_in_uV=True,
            absolute_time=True,
            glitch_threshold=100,
        )
        assert exporter.sample_rate == 1024.0
        assert exporter.range_mV == 30.0
        assert exporter.use_commas is True
        assert exporter.time_in_ms is True
        assert exporter.value_in_uV is True
        assert exporter.absolute_time is True
        assert exporter.glitch_threshold == 100

    def test_format_value_seconds(self):
        """Test value formatting for time in seconds."""
        exporter = LabChartExporter()
        result = exporter._format_value(1.234567, is_time=True)
        assert result == "1.234567"

    def test_format_value_milliseconds(self):
        """Test value formatting for time in milliseconds."""
        exporter = LabChartExporter(time_in_ms=True)
        result = exporter._format_value(1.234, is_time=True)
        assert result == "1234.000"

    def test_format_value_millivolts(self):
        """Test value formatting for voltage in millivolts."""
        exporter = LabChartExporter()
        result = exporter._format_value(1.2345, is_time=False)
        assert result == "1.2345"

    def test_format_value_microvolts(self):
        """Test value formatting for voltage in microvolts."""
        exporter = LabChartExporter(value_in_uV=True)
        result = exporter._format_value(1.234, is_time=False)
        assert result == "1234.0"

    def test_format_value_commas(self):
        """Test value formatting with European comma format."""
        exporter = LabChartExporter(use_commas=True)
        result = exporter._format_value(1.234, is_time=False)
        assert result == "1,2340"

    def test_glitch_filter_no_threshold(self):
        """Test glitch filter with threshold disabled."""
        exporter = LabChartExporter(glitch_threshold=0)
        values = [100, 200, 300, 400, 500]
        filtered = exporter._apply_glitch_filter(values)
        assert filtered == values

    def test_glitch_filter_no_glitches(self):
        """Test glitch filter with normal data."""
        exporter = LabChartExporter(glitch_threshold=500)
        values = [1000, 1010, 1020, 1030, 1040]
        filtered = exporter._apply_glitch_filter(values)
        assert filtered == values

    def test_glitch_filter_with_glitch(self):
        """Test glitch filter with a clear glitch."""
        exporter = LabChartExporter(glitch_threshold=100)
        values = [1000, 1010, 2000, 1020, 1030]  # 2000 is a glitch
        filtered = exporter._apply_glitch_filter(values)
        assert filtered[2] == 1015  # Should be average of 1010 and 1020

    def test_glitch_filter_short_array(self):
        """Test glitch filter with array too short to filter."""
        exporter = LabChartExporter(glitch_threshold=100)
        values = [100, 200]
        filtered = exporter._apply_glitch_filter(values)
        assert filtered == values

    def test_export_interval_creates_file(self):
        """Test that export_interval creates output file."""
        exporter = LabChartExporter()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_output.txt")
            signal_values = [32768, 32769, 32770, 32771]

            count = exporter.export_interval(
                filename=output_file,
                channel_num=1,
                signal_values=signal_values,
                interval_start_time=0.0,
                creation_date="2023-01-01 12:00:00",
            )

            assert count == 4
            assert os.path.exists(output_file)

            # Check file content
            with open(output_file, "r") as f:
                content = f.read()
                assert "Interval= 0.001953125" in content
                assert "DateTime= 2023-01-01 12:00:00" in content
                assert "ChannelTitle= 1" in content
                assert "Range= 120.0" in content

    def test_export_channel(self):
        """Test export_channel with multiple intervals."""
        exporter = LabChartExporter()

        with tempfile.TemporaryDirectory() as temp_dir:
            intervals = [(0.0, [32768, 32769, 32770]), (1.0, [32771, 32772, 32773])]

            output_file = exporter.export_channel(
                output_dir=temp_dir,
                channel_num=2,
                intervals=intervals,
                creation_date="2023-01-01 12:00:00",
            )

            expected_file = os.path.join(temp_dir, "E2.txt")
            assert output_file == expected_file
            assert os.path.exists(output_file)

            # Verify content
            with open(output_file, "r") as f:
                lines = f.readlines()
                assert len(lines) > 10  # Header + data lines
                assert "ChannelTitle= 2" in "".join(lines)

    def test_mV_per_count_calculation(self):
        """Test that mV per count is calculated correctly."""
        exporter = LabChartExporter(range_mV=240.0)
        expected = 240.0 / 65536.0
        assert abs(exporter.mV_per_count - expected) < 1e-10
