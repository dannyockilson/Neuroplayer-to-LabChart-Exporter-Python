"""Utilities for creating mock NDF files for testing."""

import struct
from typing import List, Tuple


def create_valid_ndf_file(
    filepath: str,
    channel: int,
    num_messages: int = 100,
    start_timestamp: int = 10000,
) -> None:
    """
    Create a valid NDF file that passes NDFReader validation.

    The file structure matches real NDF files:
    - Header at offset 0
    - Telemetry data starts at offset 20480
    - Each message is 8 bytes in the OSI telemetry format

    Args:
        filepath: Path to create the NDF file
        channel: Channel number (0-15)
        num_messages: Number of telemetry messages to write
        start_timestamp: Starting timestamp value (must be 1000-65000 for validation)
    """
    with open(filepath, "wb") as f:
        # Write minimal NDF header
        f.write(b" ndf")  # Magic bytes
        f.write(b"\x00" * 16)  # Header padding

        # Fill up to offset 20480 with zeros (standard data start offset)
        f.seek(20480)

        # Write telemetry messages
        for i in range(num_messages):
            # OSI telemetry message format (8 bytes):
            # [timestamp_low(1)] [timestamp_high(1)] [identifier(2)] [sample_data(4)]

            # Calculate timestamp (increments slowly)
            timestamp = start_timestamp + (i // 10)  # Increment every 10 messages
            timestamp = min(timestamp, 64000)  # Keep in valid range

            # Create identifier: channel in lower 4 bits, message type in next 4 bits
            # For data messages, type is typically 0 or 1
            message_type = 0
            identifier = (message_type << 4) | (channel & 0x0F)

            # Create sample data (two 16-bit values)
            # Use values around 32768 (midpoint of 16-bit range)
            sample1 = 32768 + (i % 1000)
            sample2 = 32768 - (i % 500)

            # Pack message
            message = struct.pack("<H", timestamp)  # timestamp (2 bytes)
            message += struct.pack("<H", identifier)  # identifier (2 bytes)
            message += struct.pack("<H", sample1)  # sample1 (2 bytes)
            message += struct.pack("<H", sample2)  # sample2 (2 bytes)

            f.write(message)


def create_multi_channel_ndf_file(
    filepath: str,
    channel_messages: List[Tuple[int, int]],
    start_timestamp: int = 10000,
) -> None:
    """
    Create a valid NDF file with multiple channels.

    Args:
        filepath: Path to create the NDF file
        channel_messages: List of (channel_num, num_messages) tuples
        start_timestamp: Starting timestamp value
    """
    with open(filepath, "wb") as f:
        # Write minimal NDF header
        f.write(b" ndf")
        f.write(b"\x00" * 16)

        # Fill up to offset 20480
        f.seek(20480)

        # Write messages for all channels interleaved
        timestamp = start_timestamp
        message_count = 0

        # Calculate total messages
        total_messages = sum(count for _, count in channel_messages)

        # Write messages in round-robin fashion
        channels_remaining = {ch: count for ch, count in channel_messages}

        while sum(channels_remaining.values()) > 0:
            for channel, _ in channel_messages:
                if channels_remaining[channel] > 0:
                    # Calculate timestamp (increments every ~10 messages)
                    timestamp = start_timestamp + (message_count // 10)
                    timestamp = min(timestamp, 64000)

                    # Create identifier
                    message_type = 0
                    identifier = (message_type << 4) | (channel & 0x0F)

                    # Create sample data
                    sample1 = 32768 + (message_count % 1000)
                    sample2 = 32768 - (message_count % 500)

                    # Pack and write message
                    message = struct.pack("<H", timestamp)
                    message += struct.pack("<H", identifier)
                    message += struct.pack("<H", sample1)
                    message += struct.pack("<H", sample2)

                    f.write(message)

                    channels_remaining[channel] -= 1
                    message_count += 1
