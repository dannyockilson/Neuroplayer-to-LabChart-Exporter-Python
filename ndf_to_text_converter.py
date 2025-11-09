#!/usr/bin/env python3
"""
NDF to Text Converter

Converts Neuroplayer NDF files to readable text format for inspection and
further processing. The text files can then be used with the labchart_exporter.py
to create LabChart-compatible files.

Usage:
    python ndf_to_text_converter.py input.ndf [options]
    python ndf_to_text_converter.py input_directory/ [options]

Features:
    - Converts individual NDF files or entire directories
    - Extracts all channels or specific channels
    - Creates subdirectories per NDF file with E{channel}.txt files
    - Preserves timing information and metadata
    - Handles multiple output formats
"""

import argparse
import glob
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from ndf_reader import NDFReader


class NDFToTextConverter:
    """Convert NDF files to readable text format"""

    def __init__(
        self,
        output_format: str = "simple",
        include_timestamps: bool = False,
        include_metadata: bool = True,
    ):
        """
        Initialize the converter.

        Args:
            output_format: Output format ("simple", "detailed", "csv")
            include_timestamps: Whether to include timestamp information
            include_metadata: Whether to include file metadata in output
        """
        self.output_format = output_format
        self.include_timestamps = include_timestamps
        self.include_metadata = include_metadata

    def convert_ndf_file(
        self,
        input_file: str,
        output_dir: str,
        channels: Optional[List[int]] = None,
        sample_rate: float = 512.0,
    ) -> List[str]:
        """
        Convert a single NDF file to text format.

        Args:
            input_file: Path to input NDF file
            output_dir: Output directory for text files
            channels: List of specific channels to extract (None for all)
            sample_rate: Sample rate for interval processing

        Returns:
            List of created text file paths
        """
        print(f"Processing: {os.path.basename(input_file)}")

        try:
            # Read NDF file
            reader = NDFReader(input_file)

            # Get available channels
            available_channels = reader.get_available_channels()
            if not available_channels:
                print(f"  Warning: No channels found in {input_file}")
                return []

            # Determine which channels to process
            if channels is None:
                process_channels = available_channels
            else:
                process_channels = [ch for ch in channels if ch in available_channels]
                missing = [ch for ch in channels if ch not in available_channels]
                if missing:
                    print(f"  Warning: Channels {missing} not found in file")

            if not process_channels:
                print(f"  Warning: No valid channels to process")
                return []

            print(f"  Channels: {process_channels}")
            print(f"  Creation date: {reader.get_creation_date()}")

            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Convert each channel
            created_files = []
            for channel in process_channels:
                output_file = self._convert_channel(
                    reader, channel, input_file, output_dir, sample_rate
                )
                if output_file:
                    created_files.append(output_file)

            print(f"  -> Created {len(created_files)} text files")
            return created_files

        except Exception as e:
            print(f"  Error processing {input_file}: {e}")
            return []

    def _convert_channel(
        self,
        reader: NDFReader,
        channel: int,
        input_file: str,
        output_dir: str,
        sample_rate: float,
    ) -> Optional[str]:
        """Convert a single channel to text format"""
        try:
            # Read channel data
            intervals = reader.read_channel_data(channel, sample_rate)

            if not intervals:
                print(f"    Channel {channel}: No data found")
                return None

            # Create subdirectory for this NDF file
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            file_output_dir = os.path.join(output_dir, base_name)
            os.makedirs(file_output_dir, exist_ok=True)

            # Create output filename using E{channel} naming convention
            output_file = os.path.join(file_output_dir, f"E{channel}.txt")

            # Write text file based on format
            if self.output_format == "simple":
                self._write_simple_format(output_file, intervals, reader, channel)
            elif self.output_format == "detailed":
                self._write_detailed_format(output_file, intervals, reader, channel)
            elif self.output_format == "csv":
                self._write_csv_format(output_file, intervals, reader, channel)
            else:
                raise ValueError(f"Unknown output format: {self.output_format}")

            # Get file statistics
            total_samples = sum(len(interval[1]) for interval in intervals)
            file_size = os.path.getsize(output_file)

            print(
                f"    Channel {channel}: {total_samples:,} samples -> {os.path.basename(output_file)} ({file_size:,} bytes)"
            )
            return output_file

        except Exception as e:
            print(f"    Channel {channel}: Error - {e}")
            return None

    def _write_simple_format(
        self, output_file: str, intervals: List, reader: NDFReader, channel: int
    ) -> None:
        """Write simple format (one sample value per line)"""
        with open(output_file, "w", encoding="utf-8") as f:
            # Write metadata header if requested
            if self.include_metadata:
                f.write(f"# NDF to Text Conversion\n")
                f.write(f"# Source file: {reader.filepath}\n")
                f.write(f"# Channel: {channel}\n")
                f.write(f"# Creation date: {reader.get_creation_date()}\n")
                f.write(f"# Total intervals: {len(intervals)}\n")
                f.write(
                    f"# Conversion date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("#\n")
                f.write("# Format: One sample value per line (16-bit integers)\n")
                f.write("#\n")

            # Write sample values
            for interval_time, samples in intervals:
                for sample in samples:
                    f.write(f"{sample}\n")

    def _write_detailed_format(
        self, output_file: str, intervals: List, reader: NDFReader, channel: int
    ) -> None:
        """Write detailed format (with timing and interval information)"""
        with open(output_file, "w", encoding="utf-8") as f:
            # Write metadata header
            if self.include_metadata:
                f.write(f"# NDF to Text Conversion - Detailed Format\n")
                f.write(f"# Source file: {reader.filepath}\n")
                f.write(f"# Channel: {channel}\n")
                f.write(f"# Creation date: {reader.get_creation_date()}\n")
                f.write(f"# Total intervals: {len(intervals)}\n")
                f.write(
                    f"# Conversion date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("#\n")
                f.write("# Format: [interval_time] [sample_index] [sample_value]\n")
                f.write("#\n")

            # Write detailed information
            for interval_time, samples in intervals:
                f.write(f"# Interval start: {interval_time:.6f} seconds\n")
                for i, sample in enumerate(samples):
                    if self.include_timestamps:
                        sample_time = interval_time + (i / 512.0)  # Assume 512 Hz
                        f.write(f"{sample_time:.6f} {i} {sample}\n")
                    else:
                        f.write(f"{interval_time:.6f} {i} {sample}\n")

    def _write_csv_format(
        self, output_file: str, intervals: List, reader: NDFReader, channel: int
    ) -> None:
        """Write CSV format"""
        with open(output_file, "w", encoding="utf-8") as f:
            # Write CSV header
            if self.include_timestamps:
                f.write("timestamp,interval_time,sample_index,sample_value\n")
            else:
                f.write("interval_time,sample_index,sample_value\n")

            # Write data
            for interval_time, samples in intervals:
                for i, sample in enumerate(samples):
                    if self.include_timestamps:
                        sample_time = interval_time + (i / 512.0)  # Assume 512 Hz
                        f.write(f"{sample_time:.6f},{interval_time:.6f},{i},{sample}\n")
                    else:
                        f.write(f"{interval_time:.6f},{i},{sample}\n")


def find_ndf_files(input_path: str) -> List[str]:
    """
    Find NDF files in the given path.

    Args:
        input_path: File or directory path

    Returns:
        List of NDF file paths
    """
    if os.path.isfile(input_path):
        if input_path.lower().endswith(".ndf"):
            return [input_path]
        else:
            raise ValueError(f"File {input_path} is not an NDF file")

    elif os.path.isdir(input_path):
        # Find all NDF files in directory
        pattern = os.path.join(input_path, "*.ndf")
        ndf_files = glob.glob(pattern)

        # Also check for uppercase extension
        pattern_upper = os.path.join(input_path, "*.NDF")
        ndf_files.extend(glob.glob(pattern_upper))

        return sorted(list(set(ndf_files)))  # Remove duplicates and sort

    else:
        raise FileNotFoundError(f"Path not found: {input_path}")


def bulk_convert_ndf_to_text(
    input_path: str,
    output_dir: Optional[str] = None,
    channels: Optional[List[int]] = None,
    output_format: str = "simple",
    include_timestamps: bool = False,
    include_metadata: bool = True,
    sample_rate: float = 512.0,
) -> Dict[str, List[str]]:
    """
    Convert NDF files to text format in bulk.

    Args:
        input_path: Input file or directory path
        output_dir: Output directory (default: input_path + '_text')
        channels: Specific channels to extract (None for all)
        output_format: Output format ("simple", "detailed", "csv")
        include_timestamps: Include timestamp information
        include_metadata: Include file metadata
        sample_rate: Sample rate for processing

    Returns:
        Dictionary mapping input files to created output files
    """
    # Find NDF files
    ndf_files = find_ndf_files(input_path)
    if not ndf_files:
        print(f"No NDF files found in {input_path}")
        return {}

    print(f"Found {len(ndf_files)} NDF files")

    # Set default output directory
    if output_dir is None:
        if os.path.isfile(input_path):
            output_dir = os.path.dirname(input_path) + "_text"
        else:
            output_dir = input_path.rstrip("/\\") + "_text"

    print(f"Output directory: {output_dir}")

    # Create converter
    converter = NDFToTextConverter(
        output_format=output_format,
        include_timestamps=include_timestamps,
        include_metadata=include_metadata,
    )

    # Convert each file
    results = {}
    total_files_created = 0

    for ndf_file in ndf_files:
        created_files = converter.convert_ndf_file(
            input_file=ndf_file,
            output_dir=output_dir,
            channels=channels,
            sample_rate=sample_rate,
        )
        results[ndf_file] = created_files
        total_files_created += len(created_files)

    print(f"\nConversion complete!")
    print(f"Processed {len(ndf_files)} NDF files")
    print(f"Created {total_files_created} text files")
    print(f"Output directory: {output_dir}")

    return results


def main():
    """Main entry point for command line usage"""
    parser = argparse.ArgumentParser(
        description="Convert NDF files to readable text format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file with default settings
  python ndf_to_text_converter.py data.ndf

  # Convert directory of NDF files
  python ndf_to_text_converter.py ndf_directory/

  # Convert specific channels only
  python ndf_to_text_converter.py data.ndf --channels 0 1 2

  # Create detailed format with timestamps
  python ndf_to_text_converter.py data.ndf --format detailed --timestamps

  # Create CSV output
  python ndf_to_text_converter.py data.ndf --format csv --output csv_output/

Output Formats:
  simple   - One sample value per line (compatible with TextSignalReader)
  detailed - Includes interval and timing information
  csv      - Comma-separated values format
        """,
    )

    parser.add_argument(
        "input_path", help="Input NDF file or directory containing NDF files"
    )

    parser.add_argument(
        "--output", "-o", help="Output directory (default: input_path + '_text')"
    )

    parser.add_argument(
        "--channels",
        "-c",
        type=int,
        nargs="+",
        help="Specific channels to extract (default: all channels)",
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["simple", "detailed", "csv"],
        default="simple",
        help="Output format (default: simple)",
    )

    parser.add_argument(
        "--sample-rate",
        "-sr",
        type=float,
        default=512.0,
        help="Sample rate in Hz (default: 512)",
    )

    parser.add_argument(
        "--timestamps", action="store_true", help="Include timestamp information"
    )

    parser.add_argument(
        "--no-metadata", action="store_true", help="Exclude metadata headers"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        results = bulk_convert_ndf_to_text(
            input_path=args.input_path,
            output_dir=args.output,
            channels=args.channels,
            output_format=args.format,
            include_timestamps=args.timestamps,
            include_metadata=not args.no_metadata,
            sample_rate=args.sample_rate,
        )

        if args.verbose:
            print("\nDetailed results:")
            for ndf_file, text_files in results.items():
                print(f"\n{ndf_file}:")
                for text_file in text_files:
                    file_size = (
                        os.path.getsize(text_file) if os.path.exists(text_file) else 0
                    )
                    print(f"  -> {text_file} ({file_size:,} bytes)")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
