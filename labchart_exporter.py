"""
LabChart Exporter for Neuroplayer EEG Data
Converts Neuroplayer NDF data to LabChart-compatible text format

Based on LabChart_Exporter_V4.tcl from:
https://www.opensourceinstruments.com/Electronics/A3018/Processor_Library.html
"""

import os
import struct
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class LabChartExporter:
    """Export Neuroplayer EEG data to LabChart format"""

    def __init__(
        self,
        sample_rate: float = 512.0,
        range_mV: float = 120.0,
        use_commas: bool = False,
        time_in_ms: bool = False,
        value_in_uV: bool = False,
        absolute_time: bool = False,
        glitch_threshold: int = 500,
    ):
        """
        Initialize the LabChart exporter.

        Args:
            sample_rate: Sample rate in Hz (default 512)
            range_mV: Input dynamic range in millivolts (default 120 for DC x25 transmitter)
            use_commas: Use commas instead of decimal points (European format)
            time_in_ms: Express time in milliseconds instead of seconds
            value_in_uV: Express voltage in microvolts instead of millivolts
            absolute_time: Use absolute UNIX time instead of relative time
            glitch_threshold: Threshold for glitch filtering (0 to disable)
        """
        self.sample_rate = sample_rate
        self.range_mV = range_mV
        self.mV_per_count = range_mV / 65536.0
        self.use_commas = use_commas
        self.time_in_ms = time_in_ms
        self.value_in_uV = value_in_uV
        self.absolute_time = absolute_time
        self.glitch_threshold = glitch_threshold
        self.start_time: Optional[float] = None  # Will be set on first file creation

    def _format_value(self, value: float, is_time: bool = False) -> str:
        """Format a numeric value according to settings."""
        if is_time:
            if self.time_in_ms:
                formatted = f"{value * 1000.0:.3f}"
            else:
                formatted = f"{value:.6f}"
        else:
            if self.value_in_uV:
                formatted = f"{value * 1000.0:.1f}"
            else:
                formatted = f"{value:.4f}"

        if self.use_commas:
            formatted = formatted.replace(".", ",")

        return formatted

    def _init_file(
        self, filename: str, channel_num: int, creation_date: Optional[str] = None
    ) -> None:
        """
        Initialize a LabChart export file with header information.

        Args:
            filename: Path to output file
            channel_num: Channel number
            creation_date: Creation date string (if None, uses "Unknown")
        """
        with open(filename, "w") as f:
            # Write interval (time between samples)
            if self.time_in_ms:
                interval = 1000.0 / self.sample_rate
            else:
                interval = 1.0 / self.sample_rate
            f.write(f"Interval= {interval}\n")

            # Write creation date
            if creation_date:
                f.write(f"DateTime= {creation_date}\n")
            else:
                f.write("DateTime= Unknown\n")

            # TimeFormat (specification unknown, left blank)
            f.write("TimeFormat= \n")

            # Channel title
            f.write(f"ChannelTitle= {channel_num}\n")

            # Range
            if self.value_in_uV:
                range_val = self.range_mV * 1000.0
            else:
                range_val = self.range_mV
            f.write(f"Range= {range_val:.1f}\n")

    def _apply_glitch_filter(self, values: List[int]) -> List[int]:
        """
        Apply glitch filter to remove single-sample spikes.

        Args:
            values: List of 16-bit sample values

        Returns:
            Filtered list of sample values
        """
        if self.glitch_threshold == 0 or len(values) < 3:
            return values

        filtered = values.copy()
        for i in range(1, len(values) - 1):
            # Check if current sample is a glitch (differs greatly from neighbors)
            diff_prev = abs(values[i] - values[i - 1])
            diff_next = abs(values[i] - values[i + 1])

            if diff_prev > self.glitch_threshold and diff_next > self.glitch_threshold:
                # Replace glitch with average of neighbors
                filtered[i] = (values[i - 1] + values[i + 1]) // 2

        return filtered

    def export_interval(
        self,
        filename: str,
        channel_num: int,
        signal_values: List[int],
        interval_start_time: float,
        creation_date: Optional[str] = None,
    ) -> int:
        """
        Export a single interval of data to LabChart format.

        Args:
            filename: Output file path
            channel_num: Channel number
            signal_values: List of 16-bit sample values (counts)
            interval_start_time: Start time of this interval (seconds since epoch or relative)
            creation_date: Archive creation date (for file initialization)

        Returns:
            Number of samples exported
        """
        # Initialize file if it doesn't exist
        if not os.path.exists(filename):
            self._init_file(filename, channel_num, creation_date)
            if not self.absolute_time:
                self.start_time = interval_start_time

        # Apply glitch filter if enabled
        filtered_values = self._apply_glitch_filter(signal_values)

        # Calculate start time for this interval
        if self.absolute_time:
            start_time = interval_start_time
        else:
            if self.start_time is None:
                self.start_time = interval_start_time
            start_time = interval_start_time - self.start_time

        # Generate export data
        export_lines = []
        sample_time = start_time
        sample_period = 1.0 / self.sample_rate

        for value in filtered_values:
            # Convert to millivolts (or microvolts)
            voltage = value * self.mV_per_count

            # Format time and voltage
            time_str = self._format_value(sample_time, is_time=True)
            voltage_str = self._format_value(voltage, is_time=False)

            export_lines.append(f"{time_str} {voltage_str}\n")
            sample_time += sample_period

        # Append to file
        with open(filename, "a") as f:
            f.writelines(export_lines)

        return len(filtered_values)

    def export_channel(
        self,
        output_dir: str,
        channel_num: int,
        intervals: List[Tuple[float, List[int]]],
        creation_date: Optional[str] = None,
    ) -> str:
        """
        Export all intervals for a channel to a LabChart file.

        Args:
            output_dir: Directory for output files
            channel_num: Channel number
            intervals: List of (start_time, signal_values) tuples
            creation_date: Archive creation date

        Returns:
            Path to created file
        """
        filename = os.path.join(output_dir, f"E{channel_num}.txt")

        total_samples = 0
        for start_time, signal_values in intervals:
            count = self.export_interval(
                filename, channel_num, signal_values, start_time, creation_date
            )
            total_samples += count

        print(
            f"Exported {total_samples} samples for channel {channel_num} to {filename}"
        )
        return filename

    def export_multi_channel(
        self,
        output_file: str,
        channel_data: dict,
        creation_date: Optional[str] = None,
    ) -> str:
        """
        Export multiple channels to a single unified LabChart file.

        Per-channel sample rates are auto-detected:
        - Channel 0: 128 Hz (clock signal)
        - Other channels: 512 Hz

        Args:
            output_file: Path to output file
            channel_data: Dictionary mapping channel numbers to their intervals
                         Format: {channel_num: [(start_time, signal_values), ...]}
            creation_date: Archive creation date

        Returns:
            Path to created file
        """
        if not channel_data:
            raise ValueError("No channel data provided")

        # Get all channel numbers sorted
        channels = sorted(channel_data.keys())

        # Verify all channels have data
        for channel in channels:
            if not channel_data[channel]:
                raise ValueError(f"Channel {channel} has no data")

        # Initialize file with multi-channel header
        self._init_multi_channel_file(output_file, channels, creation_date)

        # Build unified timeline
        # Collect all samples from all channels with their timestamps
        all_samples = []

        for channel in channels:
            # Determine sample rate for this channel
            # Channel 0: 128 Hz (clock signal), others: 512 Hz
            channel_sample_rate = 128.0 if channel == 0 else 512.0

            intervals = channel_data[channel]
            for start_time, signal_values in intervals:
                # Apply glitch filter if enabled
                filtered_values = self._apply_glitch_filter(signal_values)

                # Calculate time for each sample using per-channel sample rate
                sample_period = 1.0 / channel_sample_rate
                for i, value in enumerate(filtered_values):
                    sample_time = start_time + (i * sample_period)
                    all_samples.append((sample_time, channel, value))

        # Sort by timestamp to ensure proper ordering
        all_samples.sort(key=lambda x: (x[0], x[1]))

        # Group samples by timestamp using rounding for efficiency
        # Round to nearest nanosecond to handle floating point precision
        timestamp_groups: Dict[float, Dict[int, int]] = {}

        for sample_time, channel, value in all_samples:
            # Round timestamp to avoid floating point comparison issues
            # Use 9 decimal places (nanosecond precision)
            rounded_time = round(sample_time, 9)

            if rounded_time not in timestamp_groups:
                timestamp_groups[rounded_time] = {}

            timestamp_groups[rounded_time][channel] = value

        # Write unified data
        sorted_times = sorted(timestamp_groups.keys())

        # Determine start time for relative time mode
        if not self.absolute_time:
            if self.start_time is None:
                self.start_time = sorted_times[0] if sorted_times else 0.0
            # Ensure start_time is set for type checking
            start_time_value = self.start_time
        else:
            start_time_value = 0.0  # Not used in absolute mode

        with open(output_file, "a") as f:
            for sample_time in sorted_times:
                channel_values = timestamp_groups[sample_time]

                # Calculate display time
                if self.absolute_time:
                    display_time = sample_time
                else:
                    display_time = sample_time - start_time_value

                # Format time
                time_str = self._format_value(display_time, is_time=True)

                # Build line with all channel values
                line_parts = [time_str]
                for channel in channels:
                    if channel in channel_values:
                        # Convert to voltage
                        voltage = channel_values[channel] * self.mV_per_count
                        voltage_str = self._format_value(voltage, is_time=False)
                        line_parts.append(voltage_str)
                    else:
                        # Missing data - use empty or zero
                        line_parts.append("")

                f.write("\t".join(line_parts) + "\n")

        total_samples = len(sorted_times)
        print(
            f"Exported {total_samples} samples for {len(channels)} channels to {output_file}"
        )
        return output_file

    def _init_multi_channel_file(
        self, filename: str, channels: List[int], creation_date: Optional[str] = None
    ) -> None:
        """
        Initialize a multi-channel LabChart export file with header information.

        Args:
            filename: Path to output file
            channels: List of channel numbers
            creation_date: Creation date string (if None, uses "Unknown")
        """
        with open(filename, "w") as f:
            # Write interval (time between samples)
            if self.time_in_ms:
                interval = 1000.0 / self.sample_rate
            else:
                interval = 1.0 / self.sample_rate
            f.write(f"Interval= {interval}\n")

            # Write creation date
            if creation_date:
                f.write(f"DateTime= {creation_date}\n")
            else:
                f.write("DateTime= Unknown\n")

            # TimeFormat (specification unknown, left blank)
            f.write("TimeFormat= \n")

            # Channel titles - comma separated list
            channel_titles = ", ".join(str(ch) for ch in channels)
            f.write(f"ChannelTitle= {channel_titles}\n")

            # Range
            if self.value_in_uV:
                range_val = self.range_mV * 1000.0
            else:
                range_val = self.range_mV
            f.write(f"Range= {range_val:.1f}\n")


def example_usage():
    """Example of how to use the LabChart exporter"""

    # Create exporter with default settings for DC transmitter
    exporter = LabChartExporter(
        sample_rate=512.0,
        range_mV=120.0,  # DC transmitter x25 gain with 3V battery
        time_in_ms=False,
        value_in_uV=False,
        absolute_time=False,
    )

    # Example: Generate some dummy data
    # In real use, you would read this from your NDF files
    import numpy as np  # type: ignore

    # Simulate 1 second of data at 512 Hz
    num_samples = 512
    # Create a simple sine wave for demonstration (centered at 32768)
    t = np.linspace(0, 1, num_samples)
    signal = 32768 + 1000 * np.sin(2 * np.pi * 10 * t)  # 10 Hz sine wave
    signal_values = signal.astype(int).tolist()

    # Export data for channel 1
    output_dir = "./"
    creation_date = "2025-11-03 10:00:00"

    intervals = [
        (0.0, signal_values),  # First second
        (1.0, signal_values),  # Second second
    ]

    output_file = exporter.export_channel(
        output_dir=output_dir,
        channel_num=1,
        intervals=intervals,
        creation_date=creation_date,
    )

    print(f"\nExported to: {output_file}")
    print("\nFirst few lines of output:")
    with open(output_file, "r") as f:
        for i, line in enumerate(f):
            print(line.rstrip())
            if i >= 10:  # Show first 11 lines (header + a few data points)
                break


if __name__ == "__main__":
    example_usage()
