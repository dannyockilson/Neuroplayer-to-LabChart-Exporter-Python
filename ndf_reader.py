"""
NDF File Reader for Neuroplayer Data

Helper functions to read Neuroplayer NDF (Neuroscience Data Format) files
and extract signal data for export to LabChart format.
"""

import os
import struct
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class NDFReader:
    """Read Neuroplayer NDF files and extract signal data"""

    filepath: str
    metadata: Dict[str, Any]
    data_start_offset: Optional[int]
    message_size: int
    _parsed_messages: Optional[Dict[int, List[Dict]]]
    _channels_cache: Optional[List[int]]

    def __init__(self, filepath: str):
        """
        Initialize NDF reader.

        Args:
            filepath: Path to NDF file
        """
        self.filepath = filepath
        self.metadata = {}
        self.data_start_offset = None
        self.message_size = 8  # OSI telemetry messages are 8 bytes
        self._parsed_messages = None  # Cache for parsed messages grouped by channel
        self._channels_cache = None  # Cache for available channels
        self._read_metadata()
        self._find_data_section()

    def _read_metadata(self) -> None:
        """Read metadata from NDF file header"""
        with open(self.filepath, "rb") as f:
            data = f.read(1024)

            # Parse NDF header
            if len(data) >= 16:
                magic = data[0:4]
                if magic != b" ndf":
                    print(f"Warning: Unexpected magic bytes: {magic!r}")

                # Extract header values
                header_vals = struct.unpack("<III", data[4:16])
                self.metadata["header_values"] = header_vals

            # Find and parse metadata text section
            try:
                # Look for metadata markers
                start_marker = data.find(b"<c>")
                end_marker = data.find(b"</payload>")

                if start_marker >= 0 and end_marker > start_marker:
                    meta_text = data[start_marker : end_marker + 10].decode(
                        "ascii", errors="ignore"
                    )
                    self.metadata["raw_metadata"] = meta_text

                    # Extract creation date
                    if "Date Created:" in meta_text:
                        start = meta_text.index("Date Created:") + 13
                        end = meta_text.find(".", start)
                        if end > start:
                            date_str = meta_text[start:end].strip()
                            self.metadata["created"] = date_str
                        else:
                            self.metadata["created"] = "Unknown"

                    # Extract creator info
                    if "Creator:" in meta_text:
                        start = meta_text.index("Creator:") + 8
                        end = meta_text.find(".", start)
                        if end > start:
                            creator_str = meta_text[start:end].strip()
                            self.metadata["creator"] = creator_str

            except Exception as e:
                print(f"Warning: Could not parse metadata: {e}")
                self.metadata["created"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _find_data_section(self) -> None:
        """Find the start of telemetry data in the NDF file"""
        with open(self.filepath, "rb") as f:
            file_size = f.seek(0, 2)
            f.seek(0)

            # Search for telemetry data starting points
            for offset in [512, 1024, 2048, 4096, 8192, 16384, 20480]:
                if offset >= file_size:
                    continue

                f.seek(offset)
                test_data = f.read(1024)

                # Check if this region has structured data (not all zeros)
                non_zero_count = sum(1 for b in test_data if b != 0)

                if non_zero_count > 100:  # Significant data present
                    # Verify it looks like telemetry messages
                    if self._validate_telemetry_region(offset):
                        self.data_start_offset = offset
                        break

            if self.data_start_offset is None:
                print(
                    f"Warning: Could not find telemetry data section in {self.filepath}"
                )
                self.data_start_offset = 20480  # Default fallback

    def _validate_telemetry_region(self, offset: int) -> bool:
        """Check if a region contains valid telemetry data"""
        with open(self.filepath, "rb") as f:
            f.seek(offset)

            # Check first few messages for consistent structure
            valid_messages = 0
            for i in range(10):
                msg = f.read(self.message_size)
                if len(msg) < self.message_size:
                    break

                # Basic validation: not all zeros, reasonable timestamp values
                if sum(msg) > 0:
                    # Extract timestamp (first 2 bytes as 16-bit value)
                    timestamp = struct.unpack("<H", msg[0:2])[0]
                    if 1000 < timestamp < 65000:  # Reasonable timestamp range
                        valid_messages += 1

            return valid_messages >= 5

    def read_channel_data(
        self,
        channel_num: int,
        sample_rate: float = 512.0,
        message_size: Optional[int] = None,
    ) -> List[Tuple[float, List[int]]]:
        """
        Read signal data for a specific channel.

        Args:
            channel_num: Channel number to read (0-15)
            sample_rate: Expected sample rate in Hz
            message_size: Size of each telemetry message in bytes (default: 8)

        Returns:
            List of (timestamp, signal_values) tuples for each interval
        """
        if message_size is None:
            message_size = self.message_size

        if self.data_start_offset is None:
            print(f"Error: No telemetry data found in {self.filepath}")
            return []

        print(f"Reading channel {channel_num} from {self.filepath}")
        print(f"Data starts at offset {self.data_start_offset}")

        # Get grouped messages (parsed once, cached for subsequent calls)
        grouped_messages = self._parse_and_group_messages()

        # Get messages for the requested channel
        if channel_num not in grouped_messages:
            print(f"No messages found for channel {channel_num}")
            return []

        channel_messages = grouped_messages[channel_num]
        print(f"Found {len(channel_messages)} messages for channel {channel_num}")

        # Convert messages to signal intervals
        intervals = self._messages_to_intervals(channel_messages, sample_rate)

        print(f"Created {len(intervals)} intervals")
        return intervals

    def _parse_telemetry_messages(self, message_size: int) -> List[Dict]:
        """Parse all telemetry messages from the NDF file"""
        messages = []

        if self.data_start_offset is None:
            raise ValueError("No telemetry data section found in NDF file")

        with open(self.filepath, "rb") as f:
            f.seek(self.data_start_offset)

            while True:
                msg_data = f.read(message_size)
                if len(msg_data) < message_size:
                    break

                try:
                    # Parse OSI telemetry message format:
                    # [timestamp_low(1)] [timestamp_high(1)] [identifier(2)] [sample_data(4)]
                    timestamp_low = msg_data[0]
                    timestamp_high = msg_data[1]
                    timestamp = (timestamp_high << 8) | timestamp_low

                    identifier = struct.unpack("<H", msg_data[2:4])[0]
                    channel_id = identifier & 0x0F  # Lower 4 bits
                    message_type = (identifier >> 4) & 0x0F  # Next 4 bits

                    # Extract sample data (typically two 16-bit values)
                    sample1 = struct.unpack("<H", msg_data[4:6])[0]
                    sample2 = struct.unpack("<H", msg_data[6:8])[0]

                    message = {
                        "timestamp": timestamp,
                        "channel": channel_id,
                        "message_type": message_type,
                        "samples": [sample1, sample2],
                        "raw_data": msg_data,
                    }

                    messages.append(message)

                except struct.error:
                    # Skip malformed messages
                    continue

        return messages

    def _parse_and_group_messages(self) -> Dict[int, List[Dict]]:
        """
        Parse all telemetry messages once and group them by channel.
        This optimized method prevents re-parsing the file for each channel.

        Returns:
            Dictionary mapping channel_id -> list of messages for that channel
        """
        if self._parsed_messages is not None:
            return self._parsed_messages

        print("Parsing telemetry messages (one-time operation)...")
        all_messages = self._parse_telemetry_messages(self.message_size)

        # Group messages by channel
        grouped_messages: Dict[int, List[Dict]] = {}
        for msg in all_messages:
            channel_id = msg["channel"]
            if channel_id not in grouped_messages:
                grouped_messages[channel_id] = []
            grouped_messages[channel_id].append(msg)

        # Cache the results
        self._parsed_messages = grouped_messages

        # Also cache the available channels list
        self._channels_cache = sorted(grouped_messages.keys())

        print(f"Parsed {len(all_messages)} total messages across {len(grouped_messages)} channels")
        return self._parsed_messages

    def _messages_to_intervals(
        self, messages: List[Dict], sample_rate: float, interval_length: float = 1.0
    ) -> List[Tuple[float, List[int]]]:
        """Convert telemetry messages to time intervals with signal data"""
        if not messages:
            return []

        # Sort messages by timestamp
        messages.sort(key=lambda m: m["timestamp"])

        # Group messages into time intervals
        intervals = []
        samples_per_interval = int(sample_rate * interval_length)

        # Estimate timing from message timestamps
        first_timestamp = messages[0]["timestamp"]
        current_interval_samples = []
        current_interval_start = 0.0

        for i, msg in enumerate(messages):
            # Calculate relative time (convert timestamp to seconds)
            # Timestamp appears to be in some internal units, estimate conversion
            relative_time = (msg["timestamp"] - first_timestamp) / 1000.0

            # Add samples from this message
            for sample in msg["samples"]:
                # Convert from raw ADC counts (OSI uses 16-bit ADC)
                # Ensure we stay in valid 16-bit range for LabChart
                sample_value = max(0, min(65535, sample))
                current_interval_samples.append(sample_value)

            # Check if we should start a new interval
            if (
                len(current_interval_samples) >= samples_per_interval
                or i == len(messages) - 1
            ):

                if current_interval_samples:
                    # Pad or trim to exact interval size if needed
                    if len(current_interval_samples) < samples_per_interval:
                        # Pad with last value
                        last_val = current_interval_samples[-1]
                        while len(current_interval_samples) < samples_per_interval:
                            current_interval_samples.append(last_val)
                    elif len(current_interval_samples) > samples_per_interval:
                        # Trim to size
                        current_interval_samples = current_interval_samples[
                            :samples_per_interval
                        ]

                    intervals.append((current_interval_start, current_interval_samples))
                    current_interval_start += interval_length
                    current_interval_samples = []

        return intervals

    def get_creation_date(self) -> str:
        """Get the creation date from metadata"""
        return self.metadata.get("created", "Unknown")

    def get_available_channels(self) -> List[int]:
        """
        Get list of available channels in the file.
        OPTIMIZED: Uses cached channel list from parsed messages.

        Returns:
            List of channel numbers
        """
        if self.data_start_offset is None:
            return []

        # Use cached channels if available, otherwise parse and cache
        if self._channels_cache is not None:
            return self._channels_cache

        # Parse and group messages (this will also cache the channels)
        self._parse_and_group_messages()

        return self._channels_cache or []


class SimpleBinarySignalReader:
    """
    Simple reader for binary signal files (16-bit integers).
    Use this if your data is already extracted to simple binary format.
    """

    @staticmethod
    def read_signal(
        filepath: str, sample_rate: float = 512.0, interval_length: float = 1.0
    ) -> List[Tuple[float, List[int]]]:
        """
        Read a binary file of 16-bit integers and split into intervals.

        Args:
            filepath: Path to binary file
            sample_rate: Sample rate in Hz
            interval_length: Length of each interval in seconds

        Returns:
            List of (timestamp, signal_values) tuples
        """
        with open(filepath, "rb") as f:
            data = f.read()

        # Unpack as 16-bit unsigned integers
        num_samples = len(data) // 2
        values = struct.unpack(f"<{num_samples}H", data)

        # Split into intervals
        samples_per_interval = int(sample_rate * interval_length)
        intervals = []

        for i in range(0, len(values), samples_per_interval):
            interval_values = list(values[i : i + samples_per_interval])
            if len(interval_values) > 0:
                timestamp = i / sample_rate
                intervals.append((timestamp, interval_values))

        return intervals


class TextSignalReader:
    """
    Reader for text-based signal files (one value per line).
    Use this if your data is in simple text format.
    """

    @staticmethod
    def read_signal(
        filepath: str, sample_rate: float = 512.0, interval_length: float = 1.0
    ) -> List[Tuple[float, List[int]]]:
        """
        Read a text file with one sample value per line.

        Args:
            filepath: Path to text file
            sample_rate: Sample rate in Hz
            interval_length: Length of each interval in seconds

        Returns:
            List of (timestamp, signal_values) tuples
        """
        values = []
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        values.append(int(float(line)))
                    except ValueError:
                        continue

        # Split into intervals
        samples_per_interval = int(sample_rate * interval_length)
        intervals = []

        for i in range(0, len(values), samples_per_interval):
            interval_values = values[i : i + samples_per_interval]
            if len(interval_values) > 0:
                timestamp = i / sample_rate
                intervals.append((timestamp, interval_values))

        return intervals


def example_with_synthetic_data():
    """Example showing how to use readers with synthetic data"""
    import numpy as np  # type: ignore

    from labchart_exporter import LabChartExporter

    # Create some synthetic EEG-like data
    sample_rate = 512.0
    duration = 5.0  # 5 seconds
    num_samples = int(sample_rate * duration)

    # Generate signal: baseline + multiple frequency components + noise
    t = np.linspace(0, duration, num_samples)
    signal = 32768  # Baseline at middle of 16-bit range
    signal += 500 * np.sin(2 * np.pi * 10 * t)  # 10 Hz (alpha)
    signal += 200 * np.sin(2 * np.pi * 4 * t)  # 4 Hz (theta)
    signal += 100 * np.random.randn(num_samples)  # Noise

    # Convert to 16-bit integers
    signal = np.clip(signal, 0, 65535).astype(np.uint16)

    # Save as binary file for demonstration
    with open("test_signal.bin", "wb") as f:
        f.write(signal.tobytes())

    # Read back using SimpleBinarySignalReader
    intervals = SimpleBinarySignalReader.read_signal(
        "test_signal.bin",
        sample_rate=sample_rate,
        interval_length=1.0,  # 1 second intervals
    )

    print(f"Read {len(intervals)} intervals")
    print(f"First interval: {len(intervals[0][1])} samples")

    # Export to LabChart format
    exporter = LabChartExporter(sample_rate=sample_rate, range_mV=120.0)

    output_file = exporter.export_channel(
        output_dir=".",
        channel_num=1,
        intervals=intervals,
        creation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    print(f"\nExported to: {output_file}")

    # Show first few lines
    print("\nFirst few lines of LabChart file:")
    with open(output_file, "r") as f:
        for i, line in enumerate(f):
            print(line.rstrip())
            if i >= 15:
                break


def example_with_real_ndf():
    """Example showing how to use NDFReader with real NDF files"""
    import os

    from labchart_exporter import LabChartExporter

    # Example NDF file (adjust path as needed)
    ndf_files = ["mock-ndf-raw/M1555404530.ndf", "mock-ndf-raw/M1558948567.ndf"]

    for ndf_file in ndf_files:
        if not os.path.exists(ndf_file):
            continue

        print(f"\n=== Processing {ndf_file} ===")

        # Read NDF file
        reader = NDFReader(ndf_file)

        print(f"Creation date: {reader.get_creation_date()}")
        print(f"Available channels: {reader.get_available_channels()}")

        # Process first channel
        channels = reader.get_available_channels()
        if channels:
            channel = channels[0]
            print(f"\nReading channel {channel}...")

            intervals = reader.read_channel_data(channel, sample_rate=512.0)

            if intervals:
                total_samples = sum(len(interval[1]) for interval in intervals)
                print(f"Total samples: {total_samples}")

                # Export to LabChart
                exporter = LabChartExporter(sample_rate=512.0, range_mV=120.0)
                output_file = exporter.export_channel(
                    output_dir=".",
                    channel_num=channel,
                    intervals=intervals,
                    creation_date=reader.get_creation_date(),
                )

                print(f"Exported to: {output_file}")
            else:
                print("No data found")


if __name__ == "__main__":
    print("Running synthetic data example...")
    example_with_synthetic_data()

    print("\n" + "=" * 50)
    print("Running real NDF file example...")
    example_with_real_ndf()
